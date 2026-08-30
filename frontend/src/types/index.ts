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
