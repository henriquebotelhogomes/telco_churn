// Parser de CSV (com suporte a aspas) e Adapter inverso EN-US → PT-BR.
// O Adapter da API converte PT-BR → EN-US; para reutilizar /predict e
// /simulate a partir de linhas de CSV, o cockpit faz o caminho inverso
// (mapeamento determinístico de literais — a API continua recebendo PT-BR).

import type { CanonicalRow, ClientePt } from '@/types'

export function parseCsv(texto: string): Record<string, string>[] {
  const linhas: string[][] = []
  let atual: string[] = []
  let campo = ''
  let entreAspas = false

  const fecharCampo = () => {
    atual.push(campo)
    campo = ''
  }
  const fecharLinha = () => {
    fecharCampo()
    if (atual.length > 1 || atual[0] !== '') linhas.push(atual)
    atual = []
  }

  for (let i = 0; i < texto.length; i++) {
    const ch = texto[i]
    if (entreAspas) {
      if (ch === '"') {
        if (texto[i + 1] === '"') {
          campo += '"'
          i++
        } else {
          entreAspas = false
        }
      } else {
        campo += ch
      }
    } else if (ch === '"') {
      entreAspas = true
    } else if (ch === ',') {
      fecharCampo()
    } else if (ch === '\n' || ch === '\r') {
      if (ch === '\r' && texto[i + 1] === '\n') i++
      fecharLinha()
    } else {
      campo += ch
    }
  }
  if (campo !== '' || atual.length > 0) fecharLinha()

  if (linhas.length < 2) return []
  const cabecalho = linhas[0].map((c) => c.trim())
  return linhas.slice(1).map((valores) => {
    const registro: Record<string, string> = {}
    cabecalho.forEach((coluna, i) => {
      registro[coluna] = valores[i] ?? ''
    })
    return registro
  })
}

const SIM_NAO_INV: Record<string, 'Sim' | 'Não'> = { Yes: 'Sim', No: 'Não' }
const DEPENDENTE_INV: Record<string, 'Sim' | 'Não' | 'Sem serviço de internet'> = {
  Yes: 'Sim',
  No: 'Não',
  'No internet service': 'Sem serviço de internet',
}
const CONTRATO_INV: Record<string, ClientePt['contrato']> = {
  'Month-to-month': 'Mensal',
  'One year': 'Um ano',
  'Two year': 'Dois anos',
}
const PAGAMENTO_INV: Record<string, ClientePt['metodo_pagamento']> = {
  'Electronic check': 'Cheque eletrônico',
  'Mailed check': 'Cheque por correio',
  'Bank transfer (automatic)': 'Transferência bancária',
  'Credit card (automatic)': 'Cartão de crédito',
}
const INTERNET_INV: Record<string, ClientePt['servico_internet']> = {
  DSL: 'DSL',
  'Fiber optic': 'Fibra ótica',
  No: 'Não',
}

/** Converte linha canônica EN-US em payload PT-BR aceito por /predict e /simulate. */
export function canonicalToClientePt(row: Record<string, string>): ClientePt | null {
  const multiplas =
    row.MultipleLines === 'No phone service' ? 'Sem serviço de telefone' : SIM_NAO_INV[row.MultipleLines]
  const cliente: ClientePt = {
    genero: row.gender === 'Male' ? 'Masculino' : 'Feminino',
    idoso: Number(row.SeniorCitizen) === 1 ? 1 : 0,
    tem_parceiro: SIM_NAO_INV[row.Partner],
    tem_dependentes: SIM_NAO_INV[row.Dependents],
    meses_permanencia: Number(row.tenure) || 0,
    servico_telefone: SIM_NAO_INV[row.PhoneService],
    multiplas_linhas: multiplas,
    servico_internet: INTERNET_INV[row.InternetService],
    seguranca_online: DEPENDENTE_INV[row.OnlineSecurity],
    backup_online: DEPENDENTE_INV[row.OnlineBackup],
    protecao_dispositivo: DEPENDENTE_INV[row.DeviceProtection],
    suporte_tecnico: DEPENDENTE_INV[row.TechSupport],
    streaming_tv: DEPENDENTE_INV[row.StreamingTV],
    streaming_filmes: DEPENDENTE_INV[row.StreamingMovies],
    contrato: CONTRATO_INV[row.Contract],
    faturamento_sem_papel: SIM_NAO_INV[row.PaperlessBilling],
    metodo_pagamento: PAGAMENTO_INV[row.PaymentMethod],
    cobranca_mensal: Number(row.MonthlyCharges) || 0,
    cobranca_total: row.TotalCharges?.trim() === '' ? ' ' : (row.TotalCharges ?? ' '),
  }
  const incompleto = Object.values(cliente).some((v) => v === undefined)
  return incompleto ? null : cliente
}

export type { CanonicalRow }
