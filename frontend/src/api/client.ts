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
const TENANT_STORAGE = 'retainiq_tenant_id'

export function getApiKey(): string | null {
  return localStorage.getItem(API_KEY_STORAGE)
}

export function setApiKey(chave: string): void {
  if (chave.trim() === '') localStorage.removeItem(API_KEY_STORAGE)
  else localStorage.setItem(API_KEY_STORAGE, chave.trim())
}

export function getTenantId(): string {
  return localStorage.getItem(TENANT_STORAGE) || 'tenant-default'
}

export function setTenantId(tenantId: string): void {
  if (tenantId.trim() === '') localStorage.setItem(TENANT_STORAGE, 'tenant-default')
  else localStorage.setItem(TENANT_STORAGE, tenantId.trim())
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

  // Injeta automaticamente o Tenant ID ativo
  headers.set('X-Tenant-ID', getTenantId())

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

  applyPlaybook(payload: import('@/types').AplicarPlaybookRequest): Promise<import('@/types').AplicarPlaybookResponse> {
    return request('/api/v1/playbooks/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  },

  playbooksHistory(customerId?: string): Promise<import('@/types').PlaybookHistoricoItem[]> {
    const qs = customerId ? `?customer_id=${encodeURIComponent(customerId)}` : ''
    return request(`/api/v1/playbooks/history${qs}`)
  },

  temporalEvolution(): Promise<import('@/types').EvolucaoTemporalResponse> {
    return request('/api/v1/analytics/temporal-evolution')
  },

  retentionEfficiency(): Promise<import('@/types').EficienciaRetencaoResponse> {
    return request('/api/v1/analytics/retention-efficiency')
  },

  listModels(): Promise<import('@/types').ModelRegistryResponse> {
    return request('/api/v1/models')
  },

  promoteModel(modelName: string): Promise<import('@/types').PromoteModelResponse> {
    return request('/api/v1/models/promote', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_name: modelName }),
    })
  },

  shadowMetrics(): Promise<import('@/types').ShadowTelemetryResponse> {
    return request('/api/v1/models/shadow-metrics')
  },

  generateCopilotScript(
    payload: import('@/types').GenerateCopilotScriptRequest,
  ): Promise<import('@/types').GenerateCopilotScriptResponse> {
    return request('/api/v1/copilot/generate-script', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  },

  triggerAutoRetrain(
    payload?: import('@/types').AutoRetrainRequest,
  ): Promise<import('@/types').AutoRetrainResponse> {
    return request('/api/v1/admin/train/auto-retrain', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload ?? {}),
    })
  },

  listTrainingJobs(): Promise<import('@/types').TrainingJobsListResponse> {
    return request('/api/v1/admin/train/jobs')
  },

  getExecutiveReportData(): Promise<Record<string, unknown>> {
    return request('/api/v1/analytics/executive-report/data')
  },

  getStreamingStatus(): Promise<import('@/types').StreamingStatusResponse> {
    return request('/api/v1/streaming/status')
  },

  startStreaming(payload?: import('@/types').StreamingStartRequest): Promise<import('@/types').StreamingStatusResponse> {
    return request('/api/v1/streaming/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload ?? {}),
    })
  },

  stopStreaming(): Promise<import('@/types').StreamingStatusResponse> {
    return request('/api/v1/streaming/stop', {
      method: 'POST',
    })
  },

  injectStreamingChaos(payload: import('@/types').ChaosInjectionRequest): Promise<import('@/types').StreamingStatusResponse> {
    return request('/api/v1/streaming/chaos/inject', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  },

  listStreamingWindows(limit: number = 50): Promise<import('@/types').StreamingWindowsListResponse> {
    return request(`/api/v1/streaming/windows?limit=${limit}`)
  },

  getCustomerStreamingWindow(customerId: string): Promise<import('@/types').CustomerWindowMetrics> {
    return request(`/api/v1/streaming/windows/${encodeURIComponent(customerId)}`)
  },

  listRealtimeAlerts(limit: number = 50): Promise<import('@/types').RealtimeAlertsListResponse> {
    return request(`/api/v1/streaming/alerts?limit=${limit}`)
  },

  acknowledgeAlert(alertId: string, acknowledgedBy: string = 'operador'): Promise<import('@/types').AcknowledgeAlertResponse> {
    return request(`/api/v1/streaming/alerts/${encodeURIComponent(alertId)}/acknowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ acknowledged_by: acknowledgedBy }),
    })
  },

  getFeatureCatalog(): Promise<import('@/types').FeatureCatalogResponse> {
    return request('/api/v1/features/catalog')
  },

  getFeatureStoreStats(): Promise<import('@/types').FeatureStoreStatsResponse> {
    return request('/api/v1/features/stats')
  },

  getOnlineFeatures(payload: import('@/types').OnlineFeaturesRequest): Promise<import('@/types').OnlineFeaturesResponse> {
    return request('/api/v1/features/online', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  },

  materializeFeatures(payload?: import('@/types').MaterializeFeaturesRequest): Promise<import('@/types').MaterializeFeaturesResponse> {
    return request('/api/v1/features/materialize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload ?? {}),
    })
  },

  listTenants(): Promise<import('@/types').TenantListResponse> {
    return request('/api/v1/tenants')
  },

  provisionTenant(payload: import('@/types').CreateTenantRequest): Promise<import('@/types').TenantItem> {
    return request('/api/v1/tenants', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  },

  getTenantSummary(tenantId: string): Promise<import('@/types').TenantSummaryResponse> {
    return request(`/api/v1/tenants/${encodeURIComponent(tenantId)}/summary`)
  },

  getK8sClusterTopology(): Promise<import('@/types').K8sClusterTopologyResponse> {
    return request('/api/v1/ops/k8s/topology')
  },

  validateK8sManifests(): Promise<import('@/types').K8sManifestValidationResponse> {
    return request('/api/v1/ops/k8s/validate')
  },
}





