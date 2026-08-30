// Client HTTP da API RetainIQ. VITE_API_BASE_URL: dev via proxy do Vite (""),
// produção same-origin (""), ou URL explícita.

import type {
  ClientePt,
  DriftEnvelope,
  ModelInfo,
  PrevisaoBatchResponse,
  PrevisaoChurnResponse,
  SimulacaoResponse,
  AcaoSimulavel,
} from '@/types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

const API_KEY_STORAGE = 'retainiq_api_key'

export function getApiKey(): string | null {
  return localStorage.getItem(API_KEY_STORAGE)
}

export function setApiKey(chave: string): void {
  if (chave.trim() === '') localStorage.removeItem(API_KEY_STORAGE)
  else localStorage.setItem(API_KEY_STORAGE, chave.trim())
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

async function request<T>(caminho: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  const chave = getApiKey()
  if (chave) headers.set('X-API-Key', chave)

  const resposta = await fetch(`${API_BASE}${caminho}`, { ...init, headers })
  if (!resposta.ok) {
    let detalhe = resposta.statusText
    try {
      const corpo = (await resposta.json()) as { detail?: unknown }
      detalhe = typeof corpo.detail === 'string' ? corpo.detail : JSON.stringify(corpo.detail ?? corpo)
    } catch {
      // corpo não-JSON — mantém statusText
    }
    throw new ApiError(resposta.status, detalhe)
  }
  return resposta.json() as Promise<T>
}

export const api = {
  predict(cliente: ClientePt): Promise<PrevisaoChurnResponse> {
    return request('/api/v1/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cliente),
    })
  },

  predictBatchCsv(arquivo: Blob): Promise<PrevisaoBatchResponse> {
    const form = new FormData()
    form.append('file', arquivo)
    return request('/api/v1/predict/batch', { method: 'POST', body: form })
  },

  simulate(cliente: ClientePt, acoes: AcaoSimulavel[]): Promise<SimulacaoResponse> {
    return request('/api/v1/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cliente, acoes }),
    })
  },

  drift(): Promise<DriftEnvelope> {
    return request('/api/v1/metrics/drift')
  },

  driftRefresh(): Promise<DriftEnvelope> {
    return request('/api/v1/admin/drift/refresh', { method: 'POST' })
  },

  modelInfo(): Promise<ModelInfo> {
    return request('/api/v1/model/info')
  },
}
