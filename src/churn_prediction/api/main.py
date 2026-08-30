import io
from contextlib import asynccontextmanager
from typing import Any, cast

import joblib
import numpy as np
import pandas as pd
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from churn_prediction.api.schemas import (
    AcaoRecomendada,
    AcaoSimulavel,
    DistribuicaoRisco,
    LinhaInvalida,
    PrevisaoBatchLinha,
    PrevisaoBatchResponse,
    PrevisaoChurnRequest,
    PrevisaoChurnResponse,
    ResumoBatch,
    SimulacaoRequest,
    SimulacaoResponse,
    SimulacaoResultado,
)
from churn_prediction.config import settings
from churn_prediction.data.contracts import MissingColumnsError, validate_customer_batch
from churn_prediction.models import simulator

# Globais para baixa latencia (modelo + explainer em memoria)
ml_models: dict[str, Any] = {}
ml_explainers: dict[str, Any] = {}

# Nomes dos níveis na ordem dos buckets vectorizados (Baixo..Crítico)
LEVEL_NAMES = ["Baixo", "Médio", "Alto", "Crítico"]


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


def _acao_recomendada(canonical_row: dict[str, Any], model: Any) -> AcaoRecomendada | None:
    """Simula as 4 ações canônicas no simulador M2 e devolve o melhor playbook.

    Tie-break (fidelizacao > protecao > autopagamento > desconto_15) vive no simulator.
    """
    try:
        resultados = simulator.simulate_many(model, canonical_row)
        melhor = simulator.best_action(resultados)
        if melhor is None:
            return None
        playbook, descricao = simulator.PLAYBOOKS[melhor]
        return AcaoRecomendada(
            playbook=playbook,
            descricao=descricao,
            reducao_estimada_risco=round(abs(resultados[melhor]["delta_risk"]), 4),
        )
    except Exception:
        return None


def _require_model() -> Any:
    """Devolve o pipeline carregado ou 503."""
    model = ml_models.get("churn_model")
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Modelo nao carregado. Verifique se o treinamento foi executado.",
        )
    return model


def _risk_levels(probas: np.ndarray) -> np.ndarray:
    """Buckets vectorizados via thresholds centralizados: Baixo|Médio|Alto|Crítico."""
    t = settings.risk_thresholds
    return np.searchsorted([t["baixo"], t["medio"], t["alto"]], probas, side="right")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health_check():
    return {"status": "ok", "model_loaded": "churn_model" in ml_models}


@v1.post("/predict", response_model=PrevisaoChurnResponse)
def predict_churn(request: PrevisaoChurnRequest):
    """Inferência individual com SHAP, nivel de risco e playbook."""
    model = _require_model()
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
        acao = _acao_recomendada(canonical, model)
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


async def _batch_from_json(request: Request) -> tuple[pd.DataFrame, list[LinhaInvalida]]:
    """Array JSON PT-BR: Adapter por linha; itens inválidos viram linhas_invalidas."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="Corpo ausente ou JSON inválido. Envie um array de clientes ou CSV em 'file'.",
        )
    if not isinstance(body, list):
        raise HTTPException(
            status_code=422, detail="Para application/json, envie um array de clientes PT-BR."
        )

    rows: list[dict] = []
    indices: list[int] = []
    invalidas: list[LinhaInvalida] = []
    for indice, item in enumerate(body):
        try:
            rows.append(PrevisaoChurnRequest.model_validate(item).to_model_input())
            indices.append(indice)
        except ValidationError as err:
            primeiro = err.errors()[0]
            campo = ".".join(str(parte) for parte in primeiro["loc"]) or "payload"
            invalidas.append(
                LinhaInvalida(indice=indice, motivo=f"campo '{campo}': {primeiro['msg']}")
            )

    canonical = pd.DataFrame(rows, index=indices) if rows else pd.DataFrame()
    if not canonical.empty:
        resultado = validate_customer_batch(canonical)
        invalidas.extend(LinhaInvalida(**linha) for linha in resultado.invalid_rows)
        canonical = resultado.valid
    return canonical, invalidas


async def _batch_from_csv(request: Request) -> tuple[pd.DataFrame, list[LinhaInvalida]]:
    """CSV EN-US cru no campo 'file': contrato Pandera primeiro, sem Adapter."""
    form = await request.form()
    arquivo = form.get("file")
    if arquivo is None or not hasattr(arquivo, "read"):
        raise HTTPException(
            status_code=422, detail="Envie o CSV no campo 'file' (multipart/form-data)."
        )
    conteudo = await arquivo.read()
    if not conteudo.strip():
        raise HTTPException(status_code=422, detail="CSV vazio.")
    try:
        df = pd.read_csv(io.BytesIO(conteudo))
    except Exception as err:
        raise HTTPException(status_code=422, detail=f"CSV ilegível: {err}")
    if "Churn" in df.columns:
        df = df.drop(columns=["Churn"])
    try:
        resultado = validate_customer_batch(df)
    except MissingColumnsError as err:
        raise HTTPException(status_code=422, detail=str(err))
    invalidas = [LinhaInvalida(**linha) for linha in resultado.invalid_rows]
    return resultado.valid, invalidas


def _build_batch_response(
    model: Any, canonical: pd.DataFrame, invalidas: list[LinhaInvalida]
) -> PrevisaoBatchResponse:
    """Predição vectorizada do lote válido + resumo de KPIs."""
    if canonical.empty:
        resumo = ResumoBatch(
            total_analisado=0,
            total_em_risco=0,
            mrr_total_em_risco=0.0,
            distribuicao_risco=DistribuicaoRisco(baixo=0, medio=0, alto=0, critico=0),
        )
        return PrevisaoBatchResponse(results=[], resumo=resumo, linhas_invalidas=invalidas)

    try:
        probas = model.predict_proba(canonical)[:, 1]
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Erro durante a predicao em lote: {err}")

    levels = _risk_levels(probas)
    charges = pd.to_numeric(canonical["MonthlyCharges"], errors="coerce").fillna(0.0).to_numpy()
    mrr = np.where(levels >= 2, charges * probas, 0.0)
    customer_ids = (
        canonical["customerID"].astype(str).tolist() if "customerID" in canonical.columns else None
    )

    results = [
        PrevisaoBatchLinha(
            indice=int(indice),
            customer_id=customer_ids[posicao] if customer_ids is not None else None,
            previsao_cancelamento=int(probas[posicao] >= 0.5),
            probabilidade_cancelamento=float(probas[posicao]),
            nivel_risco=LEVEL_NAMES[int(levels[posicao])],
            mrr_em_risco=round(float(mrr[posicao]), 2),
        )
        for posicao, indice in enumerate(canonical.index)
    ]
    counts = np.bincount(levels, minlength=4)
    resumo = ResumoBatch(
        total_analisado=len(canonical),
        total_em_risco=int(counts[2:].sum()),
        mrr_total_em_risco=round(float(mrr.sum()), 2),
        distribuicao_risco=DistribuicaoRisco(
            baixo=int(counts[0]),
            medio=int(counts[1]),
            alto=int(counts[2]),
            critico=int(counts[3]),
        ),
    )
    return PrevisaoBatchResponse(results=results, resumo=resumo, linhas_invalidas=invalidas)


@v1.post("/predict/batch", response_model=PrevisaoBatchResponse)
async def predict_batch(request: Request):
    """Predição em lote com ingestão dupla: JSON PT-BR (Adapter) ou CSV EN-US (Pandera).

    Linhas inválidas são reportadas em ``linhas_invalidas`` sem derrubar o lote.
    """
    model = _require_model()
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        canonical, invalidas = await _batch_from_csv(request)
    else:
        canonical, invalidas = await _batch_from_json(request)

    if canonical.empty and not invalidas:
        raise HTTPException(
            status_code=422,
            detail="Forneça um array JSON de clientes ou um CSV no campo 'file'.",
        )
    return _build_batch_response(model, canonical, invalidas)


@v1.post("/simulate", response_model=SimulacaoResponse)
def simulate_churn(request: SimulacaoRequest):
    """What-If: recalcula o risco aplicando cada ação pedida via pipeline."""
    model = _require_model()
    canonical = request.cliente.to_model_input()
    try:
        resultados_brutos = simulator.simulate_many(model, canonical, request.acoes)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))

    resultados = [
        SimulacaoResultado(
            acao=cast(AcaoSimulavel, acao),
            playbook=simulator.PLAYBOOKS[acao][0],
            descricao=simulator.PLAYBOOKS[acao][1],
            original_probability=r["original_probability"],
            simulated_probability=r["simulated_probability"],
            delta_risk=r["delta_risk"],
            roi_expected_annual_savings=r["roi_expected_annual_savings"],
        )
        for acao, r in resultados_brutos.items()
    ]
    primeiro = next(iter(resultados_brutos.values()), None)
    original_p = (
        primeiro["original_probability"]
        if primeiro is not None
        else simulator.churn_probability(model, canonical)
    )
    return SimulacaoResponse(
        original_probability=original_p,
        resultados=resultados,
        melhor_acao=cast(AcaoSimulavel | None, simulator.best_action(resultados_brutos)),
    )


app.include_router(v1)
