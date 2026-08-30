from typing import Any, Literal

from pydantic import BaseModel, Field


class PrevisaoChurnRequest(BaseModel):
    """Schema de entrada da API com campos e valores 100% em português."""

    genero: Literal["Masculino", "Feminino"] = Field(..., description="Gênero do cliente")
    idoso: Literal[1, 0] = Field(..., description="É idoso? 1 para Sim, 0 para Não")
    tem_parceiro: Literal["Sim", "Não"] = Field(..., description="Possui parceiro(a)?")
    tem_dependentes: Literal["Sim", "Não"] = Field(..., description="Possui dependentes?")
    meses_permanencia: int = Field(..., ge=0, description="Meses que o cliente está na empresa")
    servico_telefone: Literal["Sim", "Não"] = Field(..., description="Tem serviço de telefone?")
    multiplas_linhas: Literal["Sim", "Não", "Sem serviço de telefone"] = Field(
        ..., description="Possui múltiplas linhas?"
    )
    servico_internet: Literal["DSL", "Fibra ótica", "Não"] = Field(
        ..., description="Tipo de provedor de internet"
    )
    seguranca_online: Literal["Sim", "Não", "Sem serviço de internet"] = Field(
        ..., description="Possui segurança online?"
    )
    backup_online: Literal["Sim", "Não", "Sem serviço de internet"] = Field(
        ..., description="Possui backup online?"
    )
    protecao_dispositivo: Literal["Sim", "Não", "Sem serviço de internet"] = Field(
        ..., description="Possui proteção de dispositivo?"
    )
    suporte_tecnico: Literal["Sim", "Não", "Sem serviço de internet"] = Field(
        ..., description="Possui suporte técnico?"
    )
    streaming_tv: Literal["Sim", "Não", "Sem serviço de internet"] = Field(
        ..., description="Possui streaming de TV?"
    )
    streaming_filmes: Literal["Sim", "Não", "Sem serviço de internet"] = Field(
        ..., description="Possui streaming de filmes?"
    )
    contrato: Literal["Mensal", "Um ano", "Dois anos"] = Field(
        ..., description="Termo de contrato do cliente"
    )
    faturamento_sem_papel: Literal["Sim", "Não"] = Field(
        ..., description="Faturamento digital (sem papel)?"
    )
    metodo_pagamento: Literal[
        "Cheque eletrônico",
        "Cheque por correio",
        "Transferência bancária",
        "Cartão de crédito",
    ] = Field(..., description="Método de pagamento")
    cobranca_mensal: float = Field(..., ge=0, description="Valor cobrado mensalmente")
    cobranca_total: str = Field(
        ..., description="Valor total cobrado (pode ser string vazia para novos clientes)"
    )

    def to_model_input(self) -> dict:
        """
        Padrão Adapter: Converte o payload em português para o formato
        original em inglês esperado pelo pipeline do scikit-learn.
        """
        map_sim_nao = {
            "Sim": "Yes",
            "Não": "No",
            "Sem serviço de internet": "No internet service",
            "Sem serviço de telefone": "No phone service",
        }

        map_internet = {
            "DSL": "DSL",
            "Fibra ótica": "Fiber optic",
            "Não": "No",
        }

        return {
            "gender": "Male" if self.genero == "Masculino" else "Female",
            "SeniorCitizen": self.idoso,
            "Partner": map_sim_nao[self.tem_parceiro],
            "Dependents": map_sim_nao[self.tem_dependentes],
            "tenure": self.meses_permanencia,
            "PhoneService": map_sim_nao[self.servico_telefone],
            "MultipleLines": map_sim_nao[self.multiplas_linhas],
            "InternetService": map_internet[self.servico_internet],
            "OnlineSecurity": map_sim_nao[self.seguranca_online],
            "OnlineBackup": map_sim_nao[self.backup_online],
            "DeviceProtection": map_sim_nao[self.protecao_dispositivo],
            "TechSupport": map_sim_nao[self.suporte_tecnico],
            "StreamingTV": map_sim_nao[self.streaming_tv],
            "StreamingMovies": map_sim_nao[self.streaming_filmes],
            "Contract": {
                "Mensal": "Month-to-month",
                "Um ano": "One year",
                "Dois anos": "Two year",
            }[self.contrato],
            "PaperlessBilling": map_sim_nao[self.faturamento_sem_papel],
            "PaymentMethod": {
                "Cheque eletrônico": "Electronic check",
                "Cheque por correio": "Mailed check",
                "Transferência bancária": "Bank transfer (automatic)",
                "Cartão de crédito": "Credit card (automatic)",
            }[self.metodo_pagamento],
            "MonthlyCharges": self.cobranca_mensal,
            "TotalCharges": self.cobranca_total,
        }


class FatorRisco(BaseModel):
    fator: str = Field(..., description="Nome do fator de negócio")
    impacto: str = Field(..., description="Impacto em % da probabilidade final (ex: +28% ou -12%)")
    shap_value: float = Field(..., description="SHAP em log-odds bruto para auditoria")
    direcao: str = Field(..., description="aumenta_risco | reduz_risco")
    descricao: str = Field(..., description="Descrição humana do driver")


class AcaoRecomendada(BaseModel):
    playbook: str = Field(..., description="Identificador do playbook recomendado")
    descricao: str = Field(..., description="Descrição da ação recomendada")
    reducao_estimada_risco: float = Field(
        ..., description="Redução absoluta de probabilidade estimada"
    )


class PrevisaoChurnResponse(BaseModel):
    previsao_cancelamento: int = Field(
        ..., description="1 se o modelo prevê que vai cancelar (Churn), 0 se não"
    )
    probabilidade_cancelamento: float = Field(
        ..., description="Probabilidade de cancelamento (0.0 a 1.0)"
    )
    nivel_risco: str = Field(..., description="Baixo | Médio | Alto | Crítico")
    mrr_em_risco: float = Field(
        ..., description="MonthlyCharges * p(churn) se Alto/Crítico, senão 0"
    )
    top_fatores_risco: list[FatorRisco] = Field(
        ..., description="Top 3 fatores SHAP ordenados por impacto"
    )
    acao_recomendada: AcaoRecomendada | None = Field(
        None, description="Playbook com maior redução de risco"
    )


# ---------------------------------------------------------------------------
# M2 — Simulador What-If
# ---------------------------------------------------------------------------

AcaoSimulavel = Literal["fidelizacao", "protecao", "autopagamento", "desconto_15"]


def _todas_acoes() -> list[AcaoSimulavel]:
    return ["fidelizacao", "protecao", "autopagamento", "desconto_15"]


class SimulacaoRequest(BaseModel):
    cliente: PrevisaoChurnRequest = Field(
        ..., description="Estado atual do cliente em PT-BR (reusa o Adapter i18n)"
    )
    acoes: list[AcaoSimulavel] = Field(
        default_factory=_todas_acoes,
        description="Ações a simular; padrão = todas as 4 canônicas",
    )


class SimulacaoResultado(BaseModel):
    acao: AcaoSimulavel
    playbook: str = Field(..., description="Identificador do playbook da ação")
    descricao: str = Field(..., description="Descrição da ação")
    original_probability: float = Field(..., description="Risco antes da ação")
    simulated_probability: float = Field(..., description="Risco após a ação")
    delta_risk: float = Field(..., description="simulated - original; negativo = redução")
    roi_expected_annual_savings: float = Field(
        ..., description="MonthlyCharges * 12 * (-delta_risk) quando delta < 0, senão 0"
    )


class SimulacaoResponse(BaseModel):
    original_probability: float = Field(..., description="Risco atual do cliente")
    resultados: list[SimulacaoResultado] = Field(..., description="Uma entrada por ação simulada")
    melhor_acao: AcaoSimulavel | None = Field(
        None, description="Ação com maior redução de risco entre as simuladas"
    )


# ---------------------------------------------------------------------------
# M2 — Predição em lote (JSON PT-BR ou CSV EN-US)
# ---------------------------------------------------------------------------


class LinhaInvalida(BaseModel):
    indice: int = Field(..., description="Posição da linha no lote enviado (-1 = nível de coluna)")
    motivo: str = Field(..., description="Motivo da rejeição")


class PrevisaoBatchLinha(BaseModel):
    indice: int = Field(..., description="Posição da linha no lote enviado")
    customer_id: str | None = Field(None, description="customerID quando presente no CSV")
    previsao_cancelamento: int
    probabilidade_cancelamento: float
    nivel_risco: str = Field(..., description="Baixo | Médio | Alto | Crítico")
    mrr_em_risco: float = Field(..., description="MonthlyCharges * p se Alto/Crítico, senão 0")


class DistribuicaoRisco(BaseModel):
    baixo: int
    medio: int
    alto: int
    critico: int


class ResumoBatch(BaseModel):
    total_analisado: int = Field(..., description="Linhas válidas analisadas")
    total_em_risco: int = Field(..., description="Clientes com nível Alto ou Crítico")
    mrr_total_em_risco: float = Field(
        ..., description="Soma de MonthlyCharges * p(churn) em Alto/Crítico"
    )
    distribuicao_risco: DistribuicaoRisco


class PrevisaoBatchResponse(BaseModel):
    results: list[PrevisaoBatchLinha]
    resumo: ResumoBatch
    linhas_invalidas: list[LinhaInvalida]


# ---------------------------------------------------------------------------
# M6 — Persistência & Closed-Loop Retention Analytics
# ---------------------------------------------------------------------------


class AplicarPlaybookRequest(BaseModel):
    customer_id: str = Field(..., description="ID do cliente alvo")
    playbook: str = Field(..., description="Nome do playbook aplicado")
    discount_pct: float = Field(default=0.0, description="Percentual de desconto concedido")
    estimated_risk_reduction: float = Field(default=0.0, description="Redução esperada de risco")
    expected_annual_savings: float = Field(default=0.0, description="Economia anual estimada em R$")
    description: str | None = Field(default=None, description="Detalhes adicionais da ação")
    applied_by: str = Field(default="analyst", description="Identificador do usuário que aplicou")
    notes: str | None = Field(default=None, description="Observações de atendimento")


class AplicarPlaybookResponse(BaseModel):
    id: int
    customer_id: str
    playbook: str
    status: str
    applied_at: str
    message: str


class PlaybookHistoricoItem(BaseModel):
    id: int
    customer_id: str
    playbook: str
    discount_pct: float
    estimated_risk_reduction: float
    expected_annual_savings: float
    applied_by: str
    status: str
    created_at: str


class RegistrarOutcomeRequest(BaseModel):
    customer_id: str
    churn_occurred: Literal[0, 1] = Field(..., description="0 para Retido, 1 para Churn")
    observed_months: int = Field(default=1, ge=1)
    actual_revenue_saved: float = Field(default=0.0, ge=0.0)
    notes: str | None = None


class RegistrarOutcomeResponse(BaseModel):
    id: int
    customer_id: str
    churn_occurred: int
    outcome_date: str
    message: str


class EvolucaoTemporalPonto(BaseModel):
    periodo: str = Field(..., description="Mês/Semana (ex: '2026-03' ou 'Semana 12')")
    total_analisado: int
    total_alto_risco: int
    total_playbooks_aplicados: int
    total_retidos_confirmados: int
    taxa_retencao_pct: float
    mrr_preservado: float


class EvolucaoTemporalResponse(BaseModel):
    pontos: list[EvolucaoTemporalPonto]
    resumo_global: dict[str, float | int]


class EficienciaPlaybook(BaseModel):
    playbook: str
    total_aplicado: int
    total_retidos: int
    total_churn: int
    taxa_sucesso_pct: float
    mrr_total_salvo: float


class EficienciaRetencaoResponse(BaseModel):
    taxa_global_eficiencia_pct: float
    total_acoes_registradas: int
    total_clientes_salvos: int
    mrr_acumulado_salvo: float
    detalhe_por_playbook: list[EficienciaPlaybook]


# ---------------------------------------------------------------------------
# M7 — Champion/Challenger, Model Registry & Shadow Scoring
# ---------------------------------------------------------------------------


class PromoteModelRequest(BaseModel):
    model_name: str = Field(..., description="Nome do modelo a ser promovido para Champion")


class PromoteModelResponse(BaseModel):
    status: str
    previous_champion: str
    new_champion: str
    promoted_at: str


class ModelRegistryItem(BaseModel):
    model_name: str
    version: str
    algo: str
    role: str = Field(..., description="champion | challenger | baseline | archived")
    trained_at: str
    artifact: str
    metrics: dict[str, Any]
    dataset: dict[str, Any]
    git_sha: str | None = None


class ModelRegistryResponse(BaseModel):
    active_champion: str
    total_models: int
    updated_at: str | None = None
    models: list[ModelRegistryItem]


class ShadowModelComparison(BaseModel):
    model_name: str
    total_samples: int
    agreement_rate_pct: float
    avg_latency_ms: float
    avg_prob_diff: float


class ShadowTelemetryResponse(BaseModel):
    total_shadow_scored: int
    avg_concordance_pct: float
    recent_samples_count: int
    model_comparisons: list[ShadowModelComparison]
    recent_events: list[dict[str, Any]]
