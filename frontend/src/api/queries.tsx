// Estado de análise em lote (MVP stateless): uma chamada POST /api/v1/predict/batch
// alimenta Dashboard, Risk Queue e Customer 360 via TanStack Query.

import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'

import { api } from '@/api/client'
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

/** Junta os resultados da API às linhas do CSV enviado (pelo índice do lote). */
export function juntarLinhas(resultado: AnalysisResult): LinhaRisco[] {
  const porIndice = new Map<number, PrevisaoBatchLinha>()
  for (const linha of resultado.resposta.results) porIndice.set(linha.indice, linha)

  const juntas: LinhaRisco[] = []
  resultado.linhas.forEach((row, indice) => {
    const previsao = porIndice.get(indice)
    if (!previsao) return
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
  const resposta = await fetch(`${import.meta.env.BASE_URL}telco_customers.csv`)
  if (!resposta.ok) throw new Error('Dataset de exemplo indisponível (public/telco_customers.csv).')
  const blob = await resposta.blob()
  return new File([blob], 'telco_customers.csv', { type: 'text/csv' })
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
}

const AnalysisContext = createContext<AnalysisContextValue | null>(null)

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [input, setInput] = useState<AnalysisInput | null>(null)

  const query = useQuery({
    queryKey: [
      'batch-analysis',
      input === null ? 'idle' : input.tipo === 'bundled' ? 'bundled' : `${input.arquivo.name}:${input.arquivo.size}`,
    ],
    queryFn: async () => {
      if (!input) throw new Error('Nenhuma fonte de análise selecionada.')
      const arquivo = input.tipo === 'bundled' ? await carregarDatasetBundled() : input.arquivo
      return analisarArquivo(arquivo)
    },
    enabled: input !== null,
    staleTime: Infinity,
    retry: false,
  })

  const valor = useMemo<AnalysisContextValue>(
    () => ({
      resultado: query.data,
      carregando: input !== null && query.isPending,
      erro: query.error instanceof Error ? query.error : null,
      isIdle: input === null,
      analisarBundled: () => setInput({ tipo: 'bundled' }),
      analisarUpload: (arquivo: File) => setInput({ tipo: 'arquivo', arquivo }),
    }),
    [query.data, query.isPending, query.error, input],
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
