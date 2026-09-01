// Tipos que espelham os schemas Pydantic da API (/api/v1) — M1 a M3.

export type NivelRisco = 'Baixo' | 'Médio' | 'Alto' | 'Crítico'

export type AcaoSimulavel = 'fidelizacao' | 'protecao' | 'autopagamento' | 'desconto_15'

// ---------------------------------------------------------------------------
// Cliente PT-BR (Adapter i18n da API)
// ---------------------------------------------------------------------------
export interface ClientePt {
  genero: 'Masculino' | 'Feminino'
  idoso: 0 | 1
  tem_parceiro: 'Sim' | 'Não'
  tem_dependentes: 'Sim' | 'Não'
  meses_permanencia: number
  servico_telefone: 'Sim' | 'Não'
  multiplas_linhas: 'Sim' | 'Não' | 'Sem serviço de telefone'
  servico_internet: 'DSL' | 'Fibra ótica' | 'Não'
  seguranca_online: 'Sim' | 'Não' | 'Sem serviço de internet'
  backup_online: 'Sim' | 'Não' | 'Sem serviço de internet'
  protecao_dispositivo: 'Sim' | 'Não' | 'Sem serviço de internet'
  suporte_tecnico: 'Sim' | 'Não' | 'Sem serviço de internet'
  streaming_tv: 'Sim' | 'Não' | 'Sem serviço de internet'
  streaming_filmes: 'Sim' | 'Não' | 'Sem serviço de internet'
  contrato: 'Mensal' | 'Um ano' | 'Dois anos'
  faturamento_sem_papel: 'Sim' | 'Não'
  metodo_pagamento:
    | 'Cheque eletrônico'
    | 'Cheque por correio'
    | 'Transferência bancária'
    | 'Cartão de crédito'
  cobranca_mensal: number
  cobranca_total: string
}

// Linha canônica EN-US (formato do CSV de treino / contrato Pandera)
export interface CanonicalRow {
  customerID?: string
  gender: string
  SeniorCitizen: string
  Partner: string
  Dependents: string
  tenure: string
  PhoneService: string
  MultipleLines: string
  InternetService: string
  OnlineSecurity: string
  OnlineBackup: string
  DeviceProtection: string
  TechSupport: string
  StreamingTV: string
  StreamingMovies: string
  Contract: string
  PaperlessBilling: string
  PaymentMethod: string
  MonthlyCharges: string
  TotalCharges: string
}

// ---------------------------------------------------------------------------
// M1 — /api/v1/predict
// ---------------------------------------------------------------------------
export interface FatorRisco {
  fator: string
  impacto: string
  shap_value: number
  direcao: 'aumenta_risco' | 'reduz_risco'
  descricao: string
}

export interface AcaoRecomendada {
  playbook: string
  descricao: string
  reducao_estimada_risco: number
}

export interface PrevisaoChurnResponse {
  previsao_cancelamento: number
  probabilidade_cancelamento: number
  nivel_risco: string
  mrr_em_risco: number
  top_fatores_risco: FatorRisco[]
  acao_recomendada: AcaoRecomendada | null
}

// ---------------------------------------------------------------------------
// M2 — /api/v1/predict/batch e /api/v1/simulate
// ---------------------------------------------------------------------------
export interface PrevisaoBatchLinha {
  indice: number
  customer_id: string | null
  previsao_cancelamento: number
  probabilidade_cancelamento: number
  nivel_risco: string
  mrr_em_risco: number
}

export interface DistribuicaoRisco {
  baixo: number
  medio: number
  alto: number
  critico: number
}

export interface ResumoBatch {
  total_analisado: number
  total_em_risco: number
  mrr_total_em_risco: number
  distribuicao_risco: DistribuicaoRisco
}

export interface LinhaInvalida {
  indice: number
  motivo: string
}

export interface PrevisaoBatchResponse {
  results: PrevisaoBatchLinha[]
  resumo: ResumoBatch
  linhas_invalidas: LinhaInvalida[]
}

export interface SimulacaoResultado {
  acao: AcaoSimulavel
  playbook: string
  descricao: string
  original_probability: number
  simulated_probability: number
  delta_risk: number
  roi_expected_annual_savings: number
}

export interface SimulacaoResponse {
  original_probability: number
  resultados: SimulacaoResultado[]
  melhor_acao: AcaoSimulavel | null
}

// ---------------------------------------------------------------------------
// M3 — observabilidade
// ---------------------------------------------------------------------------
export interface DriftFeature {
  column_type: string | null
  stattest_name: string | null
  drift_score: number | null
  drift_detected: boolean
}

export interface DriftReport {
  status: 'ok' | 'insufficient_data' | 'reference_unavailable'
  samples?: number
  min_samples?: number
  number_of_columns?: number
  number_of_drifted_columns?: number
  share_of_drifted_columns?: number
  dataset_drift?: boolean
  drift_by_feature?: Record<string, DriftFeature>
}

export interface DriftEnvelope {
  status: 'ok' | 'stale' | 'not_computed'
  generated_at: number | null
  age_seconds: number | null
  cache_ttl_seconds: number
  samples_in_buffer: number
  report: DriftReport | null
}

export interface ModelMetadata {
  model_name: string
  version: string
  algo: string
  trained_at: string
  framework_versions: Record<string, string>
  dataset: {
    path: string
    rows: number
    columns: string[]
    positive_rate: number
  }
  split: { test_size: number; random_state: number }
  metrics: Record<string, number>
  risk_thresholds: Record<string, number>
  artifact: string
  git_sha: string | null
}

export interface ModelInfo {
  model_loaded: boolean
  artifact: string
  metadata: ModelMetadata | null
}

// ---------------------------------------------------------------------------
// M6 — Persistência, Playbooks & Closed-Loop Analytics
// ---------------------------------------------------------------------------

export interface AplicarPlaybookRequest {
  customer_id: string
  playbook: string
  discount_pct?: number
  estimated_risk_reduction?: number
  expected_annual_savings?: number
  description?: string
  applied_by?: string
  notes?: string
}

export interface AplicarPlaybookResponse {
  id: number
  customer_id: string
  playbook: string
  status: string
  applied_at: string
  message: string
}

export interface PlaybookHistoricoItem {
  id: number
  customer_id: string
  playbook: string
  discount_pct: number
  estimated_risk_reduction: number
  expected_annual_savings: number
  applied_by: string
  status: string
  created_at: string
}

export interface EvolucaoTemporalPonto {
  periodo: string
  total_analisado: number
  total_alto_risco: number
  total_playbooks_aplicados: number
  total_retidos_confirmados: number
  taxa_retencao_pct: number
  mrr_preservado: number
}

export interface EvolucaoTemporalResponse {
  pontos: EvolucaoTemporalPonto[]
  resumo_global: {
    total_analisado: number
    total_acoes: number
    total_retidos: number
    taxa_global_retencao_pct: number
    mrr_total_preservado: number
  }
}

export interface EficienciaPlaybook {
  playbook: string
  total_aplicado: number
  total_retidos: number
  total_churn: number
  taxa_sucesso_pct: number
  mrr_total_salvo: number
}

export interface EficienciaRetencaoResponse {
  taxa_global_eficiencia_pct: number
  total_acoes_registradas: number
  total_clientes_salvos: number
  mrr_acumulado_salvo: number
  detalhe_por_playbook: EficienciaPlaybook[]
}

// ---------------------------------------------------------------------------
// M7 — Champion/Challenger, Model Registry & Shadow Scoring
// ---------------------------------------------------------------------------

export interface ModelRegistryItem {
  model_name: string
  version: string
  algo: string
  role: 'champion' | 'challenger' | 'baseline' | 'archived'
  trained_at: string
  artifact: string
  metrics: {
    roc_auc: number
    pr_auc: number
    f1: number
    precision: number
    recall: number
    brier_score: number
    latency_ms: number
    confusion_matrix?: number[][]
  }
  dataset: {
    path: string
    rows: number
    positive_rate: number
  }
  git_sha?: string | null
}

export interface ModelRegistryResponse {
  active_champion: string
  total_models: number
  updated_at: string | null
  models: ModelRegistryItem[]
}

export interface ShadowModelComparison {
  model_name: string
  total_samples: number
  agreement_rate_pct: number
  avg_latency_ms: number
  avg_prob_diff: number
}

export interface ShadowTelemetryResponse {
  total_shadow_scored: number
  avg_concordance_pct: number
  recent_samples_count: number
  model_comparisons: ShadowModelComparison[]
  recent_events: Array<{
    timestamp: string
    champion_name: string
    champion_prob: number
    champion_risk: string
    concordance_rate_pct: number
    challengers: Record<
      string,
      {
        probability: number
        risk_level: string
        latency_ms: number
        agrees_with_champion: boolean
        prob_difference: number
      }
    >
  }>
}

export interface PromoteModelResponse {
  status: string
  previous_champion: string
  new_champion: string
  promoted_at: string
}

// ---------------------------------------------------------------------------
// M8 — Copilot GenAI de Retenção & Smart Assistant
// ---------------------------------------------------------------------------

export interface GenerateCopilotScriptRequest {
  customer_id: string
  canal?: 'call_center' | 'whatsapp' | 'email'
  tom?: 'empatico' | 'direto' | 'consultivo'
  cliente: Record<string, unknown>
  fatores_shap?: Array<{
    fator: string
    impacto?: string
    shap_value?: number
    direcao: string
  }>
  playbook?: string
  reducao_estimada_risco?: number
  economia_esperada?: number
}

export interface GenerateCopilotScriptResponse {
  customer_id: string
  canal: string
  tom: string
  mensagem_completa: string
  roteiro_etapas?: {
    etapa_1_abertura?: string
    etapa_2_sondagem?: string
    etapa_3_proposta_valor?: string
    etapa_4_fechamento?: string
  } | null
  argumentos_chave: string[]
  playbook_aplicado: string
  provider_used: string
  latency_ms: number
}

// ---------------------------------------------------------------------------
// M9 — Continuous Training (CT) & Self-Healing Pipeline
// ---------------------------------------------------------------------------

export interface AutoRetrainRequest {
  trigger_type?: string
  auto_promote?: boolean
}

export interface AutoRetrainResponse {
  job_id: string
  status: string
  message: string
}

export interface TrainingJobItem {
  job_id: string
  trigger_type: string
  status: string
  champion_before: string
  champion_after: string
  best_candidate?: string | null
  metric_improvement: number
  created_at: string
  completed_at?: string | null
  duration_seconds: number
}

export interface TrainingJobsListResponse {
  total_jobs: number
  jobs: TrainingJobItem[]
}

// ---------------------------------------------------------------------------
// M11 & M12 — Streaming, Sliding Windows & Alertas Reativos (Fase 2)
// ---------------------------------------------------------------------------

export interface StreamingStatusResponse {
  is_running: boolean
  events_per_second: number
  chaos_mode: boolean
  buffer_size: number
  total_generated: Record<string, number>
  recent_events: Array<Record<string, unknown>>
}

export interface StreamingStartRequest {
  events_per_second?: number
}

export interface ChaosInjectionRequest {
  enable_chaos: boolean
}

export interface CustomerWindowMetrics {
  customer_id: string
  tenant_id: string
  avg_latency_15min: number
  avg_packet_loss_15min: number
  disconnect_count_1h: number
  failed_payment_count_24h: number
  negative_crm_count_7d: number
  avg_sentiment_7d: number
  realtime_instability_score: number
  last_event_timestamp: string
  total_events_processed: number
}

export interface RealtimeRiskAlert {
  alert_id: string
  customer_id: string
  severity: 'CRITICA' | 'ALTA' | 'MEDIA'
  trigger_reason: string
  recommended_intervention: string
  instability_score: number
  created_at: string
  acknowledged: boolean
  acknowledged_by?: string | null
}

export interface StreamingWindowsListResponse {
  total_customers_tracked: number
  windows: CustomerWindowMetrics[]
}

export interface RealtimeAlertsListResponse {
  total_alerts: number
  alerts: RealtimeRiskAlert[]
}

export interface AcknowledgeAlertResponse {
  success: boolean
  alert_id: string
  message: string
}

// ---------------------------------------------------------------------------
// M13 — Feature Store Unificada em Tempo Real (Feast + Redis Architecture)
// ---------------------------------------------------------------------------

export interface FeatureField {
  name: string
  dtype: 'INT' | 'FLOAT' | 'STRING' | 'BOOLEAN'
  description: string
  default_value?: unknown
}

export interface FeatureViewMetadata {
  name: string
  entity_key: string
  source_type: 'BATCH' | 'STREAM'
  ttl_seconds: number
  description: string
  features: FeatureField[]
}

export interface FeatureCatalogResponse {
  total_views: number
  feature_views: FeatureViewMetadata[]
}

export interface FeatureStoreStatsResponse {
  total_feature_views: number
  total_features_registered: number
  online_entities_count: number
  historical_log_records: number
  last_materialization: string | null
  redis_connected: boolean
  online_store_type: string
}

export interface OnlineFeaturesRequest {
  customer_ids: string[]
  feature_refs?: string[]
}

export interface OnlineFeaturesResponse {
  total_entities: number
  features: Array<Record<string, unknown>>
  retrieval_latency_ms: number
}

export interface MaterializeFeaturesRequest {
  limit?: number
}

export interface MaterializeFeaturesResponse {
  status: string
  entities_materialized: number
  total_online_entities: number
  materialized_at: string
  storage_backend: string
}

// ---------------------------------------------------------------------------
// M14 — Multi-Tenancy & Row-Level Security (RLS)
// ---------------------------------------------------------------------------

export interface TenantItem {
  tenant_id: string
  name: string
  plan: string
  rate_limit_rps: number
  status: string
  created_at: string
  custom_model_enabled: boolean
}

export interface TenantListResponse {
  total_tenants: number
  tenants: TenantItem[]
}

export interface CreateTenantRequest {
  tenant_id: string
  name: string
  plan?: string
  rate_limit_rps?: number
  custom_model_enabled?: boolean
}

export interface TenantSummaryResponse {
  tenant_id: string
  name: string
  plan: string
  status: string
  rate_limit_rps: number
  custom_model_enabled: boolean
  active_customers_count: number
  high_risk_customers_count: number
  monthly_retention_roi_brl: number
  data_isolation_level: string
}

// ---------------------------------------------------------------------------
// M15 — Kubernetes & KEDA Autoscaling (HPA / Event-Driven)
// ---------------------------------------------------------------------------

export interface K8sHpaInfo {
  min_replicas: number
  max_replicas: number
  target_cpu_utilization: string
  current_cpu_utilization: string
  target_memory_utilization: string
  current_memory_utilization: string
}

export interface K8sKedaInfo {
  min_replicas: number
  max_replicas: number
  lag_threshold: number
  current_kafka_lag: number
  topics_monitored: string[]
  cooldown_period_seconds: number
}

export interface K8sDeploymentTopology {
  name: string
  component: string
  replicas_current: number
  replicas_desired: number
  cpu_limit: string
  memory_limit: string
  autoscaling_mode: 'HPA' | 'KEDA_EVENT_DRIVEN' | string
  hpa?: K8sHpaInfo
  keda?: K8sKedaInfo
}

export interface K8sClusterTopologyResponse {
  namespace: string
  cluster_status: string
  environment: string
  deployments: K8sDeploymentTopology[]
  ingress: {
    name: string
    class: string
    host: string
    tls_enabled: boolean
  }
  services: Array<{
    name: string
    type: string
    port: number
    target_port: number
  }>
}

export interface K8sManifestValidationResponse {
  valid: boolean
  total_manifests: number
  manifests: Array<{
    filename: string
    relative_path: string
    valid: boolean
    size_bytes: number
  }>
  errors: string[]
}









