import io
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, cast

import joblib
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from churn_prediction.api import telemetry
from churn_prediction.api.schemas import (
    AcaoRecomendada,
    AcaoSimulavel,
    AplicarPlaybookRequest,
    AplicarPlaybookResponse,
    DistribuicaoRisco,
    EficienciaPlaybook,
    EficienciaRetencaoResponse,
    EvolucaoTemporalPonto,
    EvolucaoTemporalResponse,
    LinhaInvalida,
    PlaybookHistoricoItem,
    PrevisaoBatchLinha,
    PrevisaoBatchResponse,
    PrevisaoChurnRequest,
    PrevisaoChurnResponse,
    RegistrarOutcomeRequest,
    RegistrarOutcomeResponse,
    ResumoBatch,
    SimulacaoRequest,
    SimulacaoResponse,
    SimulacaoResultado,
)
from churn_prediction.config import settings
from churn_prediction.data.contracts import MissingColumnsError, validate_customer_batch
from churn_prediction.db.models import (
    CustomerOutcome,
    CustomerPrediction,
    RetentionPlaybookAction,
)
from churn_prediction.db.session import get_db, init_db
from churn_prediction.models import drift, simulator

# Globais para baixa latencia (modelo + explainer em memoria)
ml_models: dict[str, Any] = {}
ml_explainers: dict[str, Any] = {}

# Nomes dos níveis na ordem dos buckets vectorizados (Baixo..Crítico)
LEVEL_NAMES = ["Baixo", "Médio", "Alto", "Crítico"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carrega pipeline + explainer e inicializa banco de dados no startup."""
    try:
        from churn_prediction.db.seed import seed_historical_data

        await init_db()
        await seed_historical_data()
        print("Banco de dados RetainIQ inicializado")
    except Exception as e:
        print(f"Aviso na inicialização do banco: {e}")

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

# CORS via env CORS_ORIGINS (frontend Vite local + produção)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus: métricas http_* + contadores de negócio em GET /metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """X-API-Key opcional: só exige quando settings.api_key_enabled."""
    if settings.api_key_enabled and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


# Router versionado (auth opcional aplicada em todas as rotas de negócio)
v1 = APIRouter(prefix="/api/v1", tags=["v1"], dependencies=[Depends(verify_api_key)])


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

    # Telemetria M3: contadores + ring buffer (drift fora do caminho crítico)
    telemetry.predictions_total.labels(endpoint="/api/v1/predict").inc()
    telemetry.risk_level_total.labels(level=nivel).inc()
    telemetry.drift_buffer.append(canonical)

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

    # Telemetria M3: contadores + ring buffer (drift fora do caminho crítico)
    telemetry.predictions_total.labels(endpoint="/api/v1/predict/batch").inc(len(canonical))
    for nome_nivel, quantidade in zip(LEVEL_NAMES, counts):
        if quantidade:
            telemetry.risk_level_total.labels(level=nome_nivel).inc(int(quantidade))
    telemetry.drift_buffer.extend(canonical.to_dict(orient="records"))

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


@v1.get("/metrics/drift")
def metrics_drift():
    """Cache do relatório de drift. Nunca roda o Evidently (caminho crítico)."""
    return drift.get_cached_report(len(telemetry.drift_buffer))


@v1.post("/admin/drift/refresh")
def admin_drift_refresh():
    """Recalcula o drift com o ring buffer contra o dataset de treino."""
    return drift.refresh_report(telemetry.drift_buffer.to_dataframe())


@v1.get("/model/info")
def model_info():
    """Metadados do modelo gerados no treino (model_metadata.json)."""
    metadata: dict[str, Any] | None = None
    if settings.model_metadata_path.exists():
        metadata = json.loads(settings.model_metadata_path.read_text(encoding="utf-8"))
    return {
        "model_loaded": "churn_model" in ml_models,
        "artifact": str(settings.model_path),
        "metadata": metadata,
    }


# ---------------------------------------------------------------------------
# M6 — Persistência, Playbooks & Closed-Loop Analytics
# ---------------------------------------------------------------------------


@v1.post("/playbooks/apply", response_model=AplicarPlaybookResponse)
async def apply_playbook(
    request: AplicarPlaybookRequest,
    db: AsyncSession = Depends(get_db),
):
    """Registra formalmente a aplicação de um playbook de retenção para um cliente."""
    action = RetentionPlaybookAction(
        customer_id=request.customer_id,
        playbook=request.playbook,
        description=request.description,
        discount_pct=request.discount_pct,
        estimated_risk_reduction=request.estimated_risk_reduction,
        expected_annual_savings=request.expected_annual_savings,
        applied_by=request.applied_by,
        notes=request.notes,
        status="applied",
    )
    db.add(action)
    await db.commit()
    await db.refresh(action)

    return AplicarPlaybookResponse(
        id=action.id,
        customer_id=action.customer_id,
        playbook=action.playbook,
        status=action.status,
        applied_at=action.created_at.isoformat(),
        message=f"Playbook '{action.playbook}' aplicado com sucesso para o cliente {action.customer_id}.",
    )


@v1.get("/playbooks/history", response_model=list[PlaybookHistoricoItem])
async def get_playbooks_history(
    customer_id: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Retorna o histórico de playbooks aplicados com filtros opcionais."""
    stmt = select(RetentionPlaybookAction).order_by(RetentionPlaybookAction.created_at.desc())
    if customer_id:
        stmt = stmt.where(RetentionPlaybookAction.customer_id == customer_id)
    stmt = stmt.limit(limit)
    res = await db.execute(stmt)
    actions = res.scalars().all()

    return [
        PlaybookHistoricoItem(
            id=a.id,
            customer_id=a.customer_id,
            playbook=a.playbook,
            discount_pct=a.discount_pct,
            estimated_risk_reduction=a.estimated_risk_reduction,
            expected_annual_savings=a.expected_annual_savings,
            applied_by=a.applied_by,
            status=a.status,
            created_at=a.created_at.isoformat(),
        )
        for a in actions
    ]


@v1.post("/outcomes/record", response_model=RegistrarOutcomeResponse)
async def record_customer_outcome(
    request: RegistrarOutcomeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Registra o desfecho real de churn/retenção (ground truth) para fechar o ciclo analítico."""
    outcome = CustomerOutcome(
        customer_id=request.customer_id,
        churn_occurred=request.churn_occurred,
        observed_months=request.observed_months,
        actual_revenue_saved=request.actual_revenue_saved,
        notes=request.notes,
    )
    db.add(outcome)
    await db.commit()
    await db.refresh(outcome)

    status_str = "Retido" if outcome.churn_occurred == 0 else "Churn Confirmado"
    return RegistrarOutcomeResponse(
        id=outcome.id,
        customer_id=outcome.customer_id,
        churn_occurred=outcome.churn_occurred,
        outcome_date=outcome.outcome_date.isoformat(),
        message=f"Desfecho '{status_str}' registrado com sucesso para {outcome.customer_id}.",
    )


@v1.get("/analytics/temporal-evolution", response_model=EvolucaoTemporalResponse)
async def get_temporal_evolution(
    db: AsyncSession = Depends(get_db),
):
    """Calcula a evolução temporal agregada por mês das predições, intervenções e retenção real."""
    preds_res = await db.execute(
        select(CustomerPrediction).order_by(CustomerPrediction.created_at.asc())
    )
    all_preds = preds_res.scalars().all()

    actions_res = await db.execute(
        select(RetentionPlaybookAction).order_by(RetentionPlaybookAction.created_at.asc())
    )
    all_actions = actions_res.scalars().all()

    outcomes_res = await db.execute(
        select(CustomerOutcome).order_by(CustomerOutcome.outcome_date.asc())
    )
    all_outcomes = outcomes_res.scalars().all()

    periodos: dict[str, dict[str, Any]] = {}

    for p in all_preds:
        chave = p.created_at.strftime("%Y-%m")
        if chave not in periodos:
            periodos[chave] = {
                "periodo": chave,
                "total_analisado": 0,
                "total_alto_risco": 0,
                "total_playbooks_aplicados": 0,
                "total_retidos_confirmados": 0,
                "mrr_preservado": 0.0,
            }
        periodos[chave]["total_analisado"] += 1
        if p.risk_level in ("Alto", "Crítico"):
            periodos[chave]["total_alto_risco"] += 1

    for a in all_actions:
        chave = a.created_at.strftime("%Y-%m")
        if chave in periodos:
            periodos[chave]["total_playbooks_aplicados"] += 1

    for o in all_outcomes:
        chave = o.outcome_date.strftime("%Y-%m")
        if chave in periodos:
            if o.churn_occurred == 0:
                periodos[chave]["total_retidos_confirmados"] += 1
                periodos[chave]["mrr_preservado"] += o.actual_revenue_saved

    pontos: list[EvolucaoTemporalPonto] = []
    for chave in sorted(periodos.keys()):
        d = periodos[chave]
        acoes = d["total_playbooks_aplicados"]
        retidos = d["total_retidos_confirmados"]
        taxa = round((retidos / acoes * 100), 1) if acoes > 0 else 0.0
        pontos.append(
            EvolucaoTemporalPonto(
                periodo=chave,
                total_analisado=d["total_analisado"],
                total_alto_risco=d["total_alto_risco"],
                total_playbooks_aplicados=acoes,
                total_retidos_confirmados=retidos,
                taxa_retencao_pct=taxa,
                mrr_preservado=round(d["mrr_preservado"], 2),
            )
        )

    total_pred = len(all_preds)
    total_acoes = len(all_actions)
    total_ret = sum(1 for o in all_outcomes if o.churn_occurred == 0)
    taxa_global = round((total_ret / len(all_outcomes) * 100), 1) if all_outcomes else 0.0
    mrr_total_salvo = round(sum(o.actual_revenue_saved for o in all_outcomes), 2)

    return EvolucaoTemporalResponse(
        pontos=pontos,
        resumo_global={
            "total_analisado": total_pred,
            "total_acoes": total_acoes,
            "total_retidos": total_ret,
            "taxa_global_retencao_pct": taxa_global,
            "mrr_total_preservado": mrr_total_salvo,
        },
    )


@v1.get("/analytics/retention-efficiency", response_model=EficienciaRetencaoResponse)
async def get_retention_efficiency(
    db: AsyncSession = Depends(get_db),
):
    """Calcula KPIs de conversão e ROI real por playbook de retenção."""
    actions_res = await db.execute(select(RetentionPlaybookAction))
    all_actions = actions_res.scalars().all()

    outcomes_res = await db.execute(select(CustomerOutcome))
    all_outcomes = outcomes_res.scalars().all()
    outcomes_by_cust = {o.customer_id: o for o in all_outcomes}

    stats_por_playbook: dict[str, dict[str, Any]] = {}

    for action in all_actions:
        pb = action.playbook
        if pb not in stats_por_playbook:
            stats_por_playbook[pb] = {
                "playbook": pb,
                "total_aplicado": 0,
                "total_retidos": 0,
                "total_churn": 0,
                "mrr_total_salvo": 0.0,
            }
        stats_por_playbook[pb]["total_aplicado"] += 1
        outcome = outcomes_by_cust.get(action.customer_id)
        if outcome:
            if outcome.churn_occurred == 0:
                stats_por_playbook[pb]["total_retidos"] += 1
                stats_por_playbook[pb]["mrr_total_salvo"] += outcome.actual_revenue_saved
            else:
                stats_por_playbook[pb]["total_churn"] += 1

    detalhes: list[EficienciaPlaybook] = []
    for pb, s in stats_por_playbook.items():
        total_desfechos = s["total_retidos"] + s["total_churn"]
        taxa = (
            round((s["total_retidos"] / total_desfechos * 100), 1) if total_desfechos > 0 else 0.0
        )
        detalhes.append(
            EficienciaPlaybook(
                playbook=pb,
                total_aplicado=s["total_aplicado"],
                total_retidos=s["total_retidos"],
                total_churn=s["total_churn"],
                taxa_sucesso_pct=taxa,
                mrr_total_salvo=round(s["mrr_total_salvo"], 2),
            )
        )

    total_acoes = len(all_actions)
    total_retidos = sum(d.total_retidos for d in detalhes)
    total_desfechos_global = sum(d.total_retidos + d.total_churn for d in detalhes)
    taxa_global = (
        round((total_retidos / total_desfechos_global * 100), 1)
        if total_desfechos_global > 0
        else 0.0
    )
    mrr_global = round(sum(d.mrr_total_salvo for d in detalhes), 2)

    return EficienciaRetencaoResponse(
        taxa_global_eficiencia_pct=taxa_global,
        total_acoes_registradas=total_acoes,
        total_clientes_salvos=total_retidos,
        mrr_acumulado_salvo=mrr_global,
        detalhe_por_playbook=detalhes,
    )


app.include_router(v1)

# Se os arquivos estáticos do frontend (Vite) existirem, serve na raiz /
_dist_path: Path | None = None
for _cand in [
    Path("frontend/dist"),
    Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist",
]:
    if _cand.exists() and (_cand / "index.html").exists():
        _dist_path = _cand
        break

if _dist_path is not None:
    if (_dist_path / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(_dist_path / "assets")), name="assets")

    @app.get("/", include_in_schema=False)
    def root():
        index_file = _dist_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return RedirectResponse(url="/docs")

    @app.get("/favicon.svg", include_in_schema=False)
    def favicon():
        fav = _dist_path / "favicon.svg"
        if fav.exists():
            return FileResponse(fav)
        raise HTTPException(status_code=404, detail="Favicon not found")

    @app.get("/telco_customers.csv", include_in_schema=False)
    def demo_csv():
        csv_file = _dist_path / "telco_customers.csv"
        if csv_file.exists():
            return FileResponse(csv_file)
        raise HTTPException(status_code=404, detail="Demo CSV not found")
else:

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/docs")
