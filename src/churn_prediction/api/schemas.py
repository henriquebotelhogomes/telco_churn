from typing import Literal

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
