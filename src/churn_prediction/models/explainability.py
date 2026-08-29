"""M1 - RetainIQ Explainability via TreeSHAP (log-odds -> % probabilidade)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import shap
from sklearn.pipeline import Pipeline

from churn_prediction.config import settings


def sigmoid(z: np.ndarray | float) -> np.ndarray | float:
    """Sigmoid function."""
    return 1 / (1 + np.exp(-np.asarray(z)))


# Traducao tecnica -> negocio (PT-BR) - extensivel por vertical
TRANSLATE: dict[str, tuple[str, str]] = {
    "Contract_Month-to-month": ("Tipo de Contrato", "Contrato mês a mês sem fidelidade"),
    "Contract_One year": ("Tipo de Contrato", "Contrato anual"),
    "Contract_Two year": ("Tipo de Contrato", "Contrato bienal com fidelidade"),
    "InternetService_Fiber optic": ("Serviço de Internet", "Fibra ótica sem serviços de suporte"),
    "InternetService_DSL": ("Serviço de Internet", "DSL"),
    "InternetService_No": ("Serviço de Internet", "Sem serviço de internet"),
    "PaymentMethod_Electronic check": (
        "Método de Pagamento",
        "Pagamento via cheque eletrônico manual",
    ),
    "PaymentMethod_Mailed check": ("Método de Pagamento", "Cheque por correio"),
    "PaymentMethod_Bank transfer (automatic)": (
        "Método de Pagamento",
        "Transferência bancária automática",
    ),
    "PaymentMethod_Credit card (automatic)": (
        "Método de Pagamento",
        "Cartão de crédito automático",
    ),
    "OnlineSecurity_No": ("Segurança Online", "Ausência de segurança online ativa"),
    "OnlineSecurity_Yes": ("Segurança Online", "Segurança online ativa"),
    "TechSupport_No": ("Suporte Técnico", "Ausência de suporte técnico contratado"),
    "TechSupport_Yes": ("Suporte Técnico", "Suporte técnico contratado"),
    "OnlineBackup_No": ("Backup Online", "Sem backup online"),
    "DeviceProtection_No": ("Proteção de Dispositivo", "Sem proteção de dispositivo"),
    "StreamingTV_No": ("Streaming TV", "Sem streaming de TV"),
    "StreamingMovies_No": ("Streaming Filmes", "Sem streaming de filmes"),
    "tenure": ("Tempo de Permanência", "Meses como cliente"),
    "MonthlyCharges": ("Cobrança Mensal", "Valor da fatura mensal"),
    "TotalCharges": ("Cobrança Total", "Valor total acumulado"),
    "PhoneService_No": ("Telefonia", "Sem serviço de telefone"),
    "MultipleLines_No": ("Múltiplas Linhas", "Linha única"),
    "PaperlessBilling_Yes": ("Faturamento", "Faturamento sem papel"),
    "gender_Male": ("Gênero", "Masculino"),
    "gender_Female": ("Gênero", "Feminino"),
    "SeniorCitizen_1": ("Idoso", "Cliente idoso"),
    "Partner_Yes": ("Parceiro", "Tem parceiro"),
    "Dependents_Yes": ("Dependentes", "Tem dependentes"),
}


def nivel_risco(p: float) -> str:
    """Retorna nivel semantico baseado em settings.risk_thresholds."""
    t = settings.risk_thresholds
    if p < t["baixo"]:
        return "Baixo"
    if p < t["medio"]:
        return "Médio"
    if p < t["alto"]:
        return "Alto"
    return "Crítico"


class ChurnExplainer:
    """Calcula SHAP local e converte para % de probabilidade."""

    def __init__(self, pipeline: Pipeline) -> None:
        # Extrai preprocessador e modelo do pipeline treinado
        if "preprocessing" in pipeline.named_steps:
            self.preprocessor = pipeline.named_steps["preprocessing"]
        elif "preprocessing" in str(pipeline):
            # fallback
            self.preprocessor = pipeline.named_steps[list(pipeline.named_steps.keys())[0]]
        else:
            self.preprocessor = pipeline.named_steps["preprocessing"]
        self.model = pipeline.named_steps["classifier"]
        # TreeExplainer em log-odds (raw)
        self.explainer = shap.TreeExplainer(self.model, model_output="raw")
        self.feature_names = self._get_feature_names()

    def _get_feature_names(self) -> list[str]:
        """Obtem nomes das features transformadas, removendo prefixo do ColumnTransformer."""
        try:
            # preprocessor é Pipeline(cleaner, preprocessor=ColumnTransformer)
            if (
                hasattr(self.preprocessor, "named_steps")
                and "preprocessor" in self.preprocessor.named_steps
            ):
                ct = self.preprocessor.named_steps["preprocessor"]
                names = ct.get_feature_names_out().tolist()
            else:
                names = self.preprocessor.get_feature_names_out().tolist()
            # Remove prefixo "num__" / "cat__"
            cleaned = [n.split("__")[-1] for n in names]
            return cleaned
        except Exception:
            # Fallback: usa indices
            try:
                n_features = self.explainer.expected_value  # dummy
                _ = n_features
            except Exception:
                pass
            return [f"feature_{i}" for i in range(100)]

    def _translate(self, feature: str) -> tuple[str, str]:
        """Retorna (fator, descricao) amigavel."""
        if feature in TRANSLATE:
            return TRANSLATE[feature]
        # Heuristica: prefix matching
        for k, v in TRANSLATE.items():
            if feature.startswith(k.split("_")[0]):
                # tenta mapear generico
                pass
        # Fallback: humaniza nome tecnico
        fator = feature.replace("_", " ").replace("(", "").replace(")", "").title()
        descricao = f"Impacto de {feature}"
        # Tenta mapear por contem
        for k, (f, d) in TRANSLATE.items():
            if k.lower() in feature.lower() or feature.lower() in k.lower():
                return (f, d)
        return (fator, descricao)

    def explain_instance(self, raw_input_df: pd.DataFrame) -> list[dict]:
        """
        1. Transforma raw_input_df via preprocessor.
        2. Calcula shap_values.
        3. Converte log-odds -> % via sigmoid cumulativo.
        4. Retorna Top 3 ordenado por |impacto|.
        """
        # 1. Transform
        transformed = self.preprocessor.transform(raw_input_df)
        # 2. SHAP
        shap_values = self.explainer.shap_values(transformed)
        if isinstance(shap_values, list):
            # binary classification: lista com [class0, class1]
            shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        shap_values = np.array(shap_values).flatten()
        base_value = self.explainer.expected_value
        if isinstance(base_value, (list, np.ndarray)):
            if isinstance(base_value, np.ndarray) and base_value.size > 1:
                base_value = float(base_value[1])
            elif isinstance(base_value, list) and len(base_value) > 1:
                base_value = float(base_value[1])
            else:
                base_value = float(np.asarray(base_value).flatten()[0])
        else:
            base_value = float(base_value)

        # Garante tamanho compativel
        if len(shap_values) != len(self.feature_names):
            # Trunca ou padroniza
            min_len = min(len(shap_values), len(self.feature_names))
            shap_values = shap_values[:min_len]
            feature_names = self.feature_names[:min_len]
        else:
            feature_names = self.feature_names

        # 3. Conversao para % via sigmoid cumulativo
        # Ordena por |phi| decrescente mas mantem phi alinhado
        idx = np.argsort(-np.abs(shap_values))
        phi_sorted = shap_values[idx]
        names_sorted = [feature_names[i] for i in idx]

        p_final = float(sigmoid(base_value + float(np.sum(shap_values))))
        if p_final == 0:
            p_final = 1e-9

        impacts: list[dict] = []
        cum = base_value
        p_prev = float(sigmoid(cum))
        for i, phi in enumerate(phi_sorted[:5]):
            cum += float(phi)
            p_cur = float(sigmoid(cum))
            impacto = (p_cur - p_prev) / p_final
            fator, descricao = self._translate(names_sorted[i])
            impacts.append(
                {
                    "fator": fator,
                    "impacto": f"{impacto:+.0%}",
                    "shap_value": round(float(phi), 3),
                    "direcao": "aumenta_risco" if phi > 0 else "reduz_risco",
                    "descricao": descricao,
                }
            )
            p_prev = p_cur

        # Ordena por magnitude de impacto e pega top 3
        impacts = sorted(
            impacts,
            key=lambda x: abs(float(x["impacto"].strip("%+").replace("+", "").replace("-", ""))),
            reverse=True,
        )[:3]
        return impacts
