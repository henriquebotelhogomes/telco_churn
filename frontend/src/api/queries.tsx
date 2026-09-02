// queries.tsx — hook unificado de análise em lote (AnalysisProvider)
// alimenta Dashboard, Risk Queue e Customer 360 via TanStack Query.

import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { api, getTenantId } from '@/api/client'
import { parseCsv } from '@/lib/csv'
import type { PrevisaoBatchLinha, PrevisaoBatchResponse } from '@/types'

export interface AnalysisResult {
  fonte: string
  linhas: Record<string, string>[]
  resposta: PrevisaoBatchResponse
}

export interface LinhaRisco {
  indice: number
  customerId: string
  tenure: number
  contract: string
  monthlyCharges: number
  probabilidade: number
  nivel: string
  previsao: number
  mrrEmRisco: number
  row: Record<string, string>
}

/** Junta o CSV original com as predições alinhadas por índice (1:1). */
export function juntarLinhas(analise: AnalysisResult): LinhaRisco[] {
  const juntas: LinhaRisco[] = []
  analise.resposta.results.forEach((previsao: PrevisaoBatchLinha, i: number) => {
    const indice = previsao.indice ?? i
    const row = analise.linhas[indice]
    if (!row) return
    juntas.push({
      indice,
      customerId: previsao.customer_id ?? row.customerID ?? `#${indice}`,
      tenure: Number(row.tenure) || 0,
      contract: row.Contract ?? '—',
      monthlyCharges: Number(row.MonthlyCharges) || 0,
      probabilidade: previsao.probabilidade_cancelamento,
      nivel: previsao.nivel_risco,
      previsao: previsao.previsao_cancelamento,
      mrrEmRisco: previsao.mrr_em_risco,
      row,
    })
  })
  return juntas
}

type AnalysisInput = { tipo: 'bundled' } | { tipo: 'arquivo'; arquivo: File }

async function carregarDatasetBundled(): Promise<File> {
  const cacheBuster = `?t=${Date.now()}`
  let resposta = await fetch(`${import.meta.env.BASE_URL}telco_enterprise_customers.csv${cacheBuster}`, {
    cache: 'no-cache',
  })
  if (!resposta.ok) {
    resposta = await fetch(`${import.meta.env.BASE_URL}telco_customers.csv${cacheBuster}`, {
      cache: 'no-cache',
    })
  }
  if (!resposta.ok) throw new Error('Dataset de exemplo indisponível (telco_enterprise_customers.csv).')
  const texto = await resposta.text()

  const tenantId = getTenantId()
  if (tenantId === 'tenant-default') {
    return new File([texto], 'telco_enterprise_global.csv', { type: 'text/csv' })
  }

  // Particionamento por operadora (Row-Level Security)
  const linhas = texto.trim().split('\n')
  const cabecalho = linhas[0]
  const dados = linhas.slice(1)

  let modulo: number
  let resto: number
  let prefixo: string
  let nomeArquivo: string

  if (tenantId === 'tenant-vivo') {
    prefixo = 'VIVO'
    modulo = 3
    resto = 0
    nomeArquivo = 'telco_enterprise_vivo.csv'
  } else if (tenantId === 'tenant-claro') {
    prefixo = 'CLARO'
    modulo = 3
    resto = 1
    nomeArquivo = 'telco_enterprise_claro.csv'
  } else if (tenantId === 'tenant-tim') {
    prefixo = 'TIM'
    modulo = 3
    resto = 2
    nomeArquivo = 'telco_enterprise_tim.csv'
  } else {
    prefixo = tenantId.replace('tenant-', '').toUpperCase()
    modulo = 4
    resto = 0
    nomeArquivo = `telco_enterprise_${prefixo.toLowerCase()}.csv`
  }

  const linhasFiltradas = dados
    .filter((linha, index) => {
      // Se a linha já tem coluna operator (ex: Vivo, Claro, TIM)
      if (linha.includes('Vivo') && tenantId === 'tenant-vivo') return true
      if (linha.includes('Claro') && tenantId === 'tenant-claro') return true
      if (linha.includes('TIM') && tenantId === 'tenant-tim') return true
      return index % modulo === resto
    })
    .map((linha) => {
      const colunas = linha.split(',')
      if (!colunas[0].startsWith(prefixo)) {
        colunas[0] = `${prefixo}-${colunas[0]}`
      }
      return colunas.join(',')
    })

  const novoConteudoCsv = [cabecalho, ...linhasFiltradas].join('\n')
  return new File([novoConteudoCsv], nomeArquivo, { type: 'text/csv' })
}

async function analisarArquivo(arquivo: File): Promise<AnalysisResult> {
  const [texto, resposta] = await Promise.all([arquivo.text(), api.predictBatchCsv(arquivo)])
  return { fonte: arquivo.name, linhas: parseCsv(texto), resposta }
}

interface AnalysisContextValue {
  resultado: AnalysisResult | undefined
  carregando: boolean
  erro: Error | null
  isIdle: boolean
  analisarBundled: () => void
  analisarUpload: (arquivo: File) => void
  carregarDatasetTexto: (nome: string, textoCsv: string) => void
}

const AnalysisContext = createContext<AnalysisContextValue | null>(null)

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [version, setVersion] = useState(1)
  const [input, setInput] = useState<AnalysisInput | null>({ tipo: 'bundled' })

  const query = useQuery({
    queryKey: [
      'batch-analysis',
      version,
      input === null
        ? 'idle'
        : input.tipo === 'bundled'
          ? `bundled:${getTenantId()}`
          : `${input.arquivo.name}:${input.arquivo.size}:${getTenantId()}`,
    ],
    queryFn: async () => {
      if (!input) throw new Error('Nenhuma fonte de análise selecionada.')
      const arquivo = input.tipo === 'bundled' ? await carregarDatasetBundled() : input.arquivo
      return analisarArquivo(arquivo)
    },
    enabled: input !== null,
    staleTime: 0,
    gcTime: 0,
    retry: false,
  })

  const valor = useMemo<AnalysisContextValue>(
    () => ({
      resultado: query.data,
      carregando: input !== null && query.isPending,
      erro: query.error instanceof Error ? query.error : null,
      isIdle: input === null,
      analisarBundled: () => {
        setVersion((v) => v + 1)
        setInput({ tipo: 'bundled' })
        queryClient.invalidateQueries({ queryKey: ['batch-analysis'] })
      },
      analisarUpload: (arquivo: File) => {
        setVersion((v) => v + 1)
        setInput({ tipo: 'arquivo', arquivo })
      },
      carregarDatasetTexto: (nome: string, textoCsv: string) => {
        setVersion((v) => v + 1)
        const file = new File([textoCsv], nome, { type: 'text/csv' })
        setInput({ tipo: 'arquivo', arquivo: file })
      },
    }),
    [query.data, query.isPending, query.error, input, queryClient],
  )

  return <AnalysisContext.Provider value={valor}>{children}</AnalysisContext.Provider>
}

export function useAnalysis(): AnalysisContextValue {
  const ctx = useContext(AnalysisContext)
  if (!ctx) throw new Error('useAnalysis deve ser usado dentro de <AnalysisProvider>.')
  return ctx
}

export function useModelInfo() {
  return useQuery({ queryKey: ['model-info'], queryFn: api.modelInfo, staleTime: 60_000 })
}

export function useDrift() {
  return useQuery({ queryKey: ['drift'], queryFn: api.drift, staleTime: 30_000 })
}
