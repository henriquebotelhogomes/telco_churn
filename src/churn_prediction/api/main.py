from contextlib import asynccontextmanager
from typing import Any

import joblib
import pandas as pd
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from churn_prediction.api.schemas import (
    AcaoRecomendada,
    PrevisaoChurnRequest,
    PrevisaoChurnResponse,
)
from churn_prediction.config import settings

# Globais para baixa latencia (modelo + explainer em memoria)
ml_models: dict[str, Any] = {}
ml_explainers: dict[str, Any] = {}

PLAYBOOKS: dict[str, tuple[str, str]] = {
    "fidelizacao": (
        "MIGRACAO_CONTRATO_ANUAL",
        "Oferecer 15% de desconto no plano anual com inclusao de Suporte Tecnico.",
    ),
    "protecao": ("CROSS_SELL_PROTECAO", "Ativar Suporte Tecnico e Seguranca Online."),
    "autopagamento": (
        "AUTOMATIZACAO_PAGAMENTO",
        "Migrar para pagamento automatico via cartao de credito.",
    ),
    "desconto": ("DESCONTO_RETENCAO", "Oferecer 15% de desconto na mensalidade."),
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carrega pipeline + explainer no startup."""
    try:
        model = joblib.load(settings.model_path)
        ml_models["churn_model"] = model
        print(f"Modelo carregado: {settings.model_path}")
        # Tenta criar explainer (SHAP) — falha nao bloqueia API
        try:
            from churn_prediction.models.explainability import ChurnExplainer

            ml_explainers["churn_explainer"] = ChurnExplainer(model)
            print("Explainer SHAP carregado")
        except Exception as e:
            print(f"Aviso: falha ao criar explainer SHAP: {e}")
    except Exception as e:
        print(f"Erro ao carregar modelo. Rode train.py. Detalhes: {e}")
    yield
    ml_models.clear()
    ml_explainers.clear()


app = FastAPI(
    title="RetainIQ - Telco Churn Prediction API",
    description="API RetainIQ: predicao de churn com SHAP, nivel de risco e playbook recomendado",
    version="1.0.0",
    lifespan=lifespan,
)

# Router versionado
v1 = APIRouter(prefix="/api/v1", tags=["v1"])


def _nivel_risco(p: float) -> str:
    from churn_prediction.models.explainability import nivel_risco

    return nivel_risco(p)


def _acao_recomendada(
    canonical_row: dict[str, Any], model: Any
) -> tuple[AcaoRecomendada | None, list[dict]]:
    """Simula 4 acoes e retorna a de maior reducao absoluta.

    Tie-break: fidelizacao > protecao > autopagamento > desconto.
    """
    orig_p = float(model.predict_proba(pd.DataFrame([canonical_row]))[0][1])

    mutations: dict[str, dict[str, Any]] = {
        "fidelizacao": {**canonical_row, "Contract": "Two year"},
        "protecao": {**canonical_row, "TechSupport": "Yes", "OnlineSecurity": "Yes"},
        "autopagamento": {**canonical_row, "PaymentMethod": "Credit card (automatic)"},
        "desconto": {
            **canonical_row,
            "MonthlyCharges": float(canonical_row["MonthlyCharges"]) * 0.85,
        },
    }
    # Ajusta TotalCharges proporcional se desconto? Nao — deixa como esta (pipeline limpa)
    results: list[dict] = []
    best_key: str | None = None
    best_delta: float = 0.0

    order = ["fidelizacao", "protecao", "autopagamento", "desconto"]
    for key in order:
        try:
            mutated = mutations[key]
            sim_p = float(model.predict_proba(pd.DataFrame([mutated]))[0][1])
            delta = sim_p - orig_p  # negativo = bom
            results.append({"key": key, "delta": delta, "p": sim_p})
            if best_key is None or delta < best_delta - 1e-9:
                best_key = key
                best_delta = delta
        except Exception:
            continue

    if best_key is None or best_delta >= -1e-9:
        # Nenhuma acao reduziu risco
        return None, results

    playbook, descricao = PLAYBOOKS[best_key]
    return AcaoRecomendada(
        playbook=playbook,
        descricao=descricao,
        reducao_estimada_risco=round(abs(float(best_delta)), 4),
    ), results


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": "churn_model" in ml_models}


@v1.post("/predict", response_model=PrevisaoChurnResponse)
def predict_churn(request: PrevisaoChurnRequest):
    """Inferência individual com SHAP, nivel de risco e playbook."""
    model = ml_models.get("churn_model")
    if not model:
        raise HTTPException(
            status_code=503,
            detail="Modelo nao carregado. Verifique se o treinamento foi executado.",
        )
    canonical = request.to_model_input()
    input_data = pd.DataFrame([canonical])

    try:
        prediction = int(model.predict(input_data)[0])
        probability = float(model.predict_proba(input_data)[0][1])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro durante a predicao: {str(e)}")

    # Nivel de risco + MRR em risco
    nivel = _nivel_risco(probability)
    mrr = float(canonical["MonthlyCharges"]) * probability if nivel in ("Alto", "Crítico") else 0.0

    # SHAP Top 3
    top_fatores: list[dict] = []
    explainer = ml_explainers.get("churn_explainer")
    if explainer is not None:
        try:
            top_fatores = explainer.explain_instance(input_data)
        except Exception:
            top_fatores = []

    # Acao recomendada (simula 4 acoes)
    acao: AcaoRecomendada | None = None
    try:
        acao, _ = _acao_recomendada(canonical, model)
    except Exception:
        acao = None

    return PrevisaoChurnResponse(
        previsao_cancelamento=prediction,
        probabilidade_cancelamento=probability,
        nivel_risco=nivel,
        mrr_em_risco=round(mrr, 2),
        top_fatores_risco=top_fatores,  # type: ignore[arg-type]
        acao_recomendada=acao,
    )


app.include_router(v1)
