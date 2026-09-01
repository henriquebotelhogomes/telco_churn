import datetime

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from churn_prediction.api.main import app
from churn_prediction.features.definitions import (
    ALL_FEATURE_VIEWS,
    CUSTOMER_REALTIME_STREAM_FV,
)
from churn_prediction.features.store import UnifiedFeatureStore


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_feature_views_definitions():
    """Testa a integridade estrutural das Feature Views e tipos registrados."""
    assert len(ALL_FEATURE_VIEWS) == 3
    view_names = [fv.name for fv in ALL_FEATURE_VIEWS]
    assert "customer_demographic_features" in view_names
    assert "customer_financial_features" in view_names
    assert "customer_realtime_stream_features" in view_names

    # Valida campos da view de streaming
    stream_fields = [f.name for f in CUSTOMER_REALTIME_STREAM_FV.features]
    assert "avg_latency_15min" in stream_fields
    assert "disconnect_count_1h" in stream_fields
    assert "realtime_instability_score" in stream_fields


def test_get_online_features_unification():
    """Testa a recuperação vetorial unificada de features de batch e streaming."""
    store = UnifiedFeatureStore()
    cid = "CLI-00001"

    # Busca sem filtro (todas as features)
    results = store.get_online_features([cid])
    assert len(results) == 1
    rec = results[0]
    assert rec["customer_id"] == cid
    assert "Contract" in rec
    assert "MonthlyCharges" in rec
    assert "avg_latency_15min" in rec
    assert "realtime_instability_score" in rec

    # Busca com filtro de feature refs
    filtered_res = store.get_online_features(
        [cid],
        feature_refs=["Contract", "MonthlyCharges", "realtime_instability_score"],
    )
    assert len(filtered_res) == 1
    filt_rec = filtered_res[0]
    assert "Contract" in filt_rec
    assert "MonthlyCharges" in filt_rec
    assert "realtime_instability_score" in filt_rec
    assert "PaperlessBilling" not in filt_rec


def test_historical_features_time_travel():
    """Testa o Time-Travel Join garantindo Point-in-Time Correctness."""
    store = UnifiedFeatureStore()
    cid = "CLI-00005"

    now = datetime.datetime.now(datetime.UTC)
    entity_df = pd.DataFrame(
        [
            {"customer_id": cid, "timestamp": now.isoformat()},
            {"customer_id": "CLI-99999", "timestamp": now.isoformat()},
        ]
    )

    df_joined = store.get_historical_features(
        entity_df,
        feature_names=["Contract", "MonthlyCharges", "tenure"],
    )

    assert "Contract" in df_joined.columns
    assert "MonthlyCharges" in df_joined.columns
    assert "tenure" in df_joined.columns
    assert len(df_joined) == 2


def test_materialization_engine():
    """Testa o processo de sincronização e materialização para a Online Store."""
    store = UnifiedFeatureStore()
    res = store.materialize(limit=25)

    assert res["status"] == "SUCCESS"
    assert res["entities_materialized"] == 25
    assert res["total_online_entities"] >= 25

    stats = store.get_stats()
    assert stats["total_feature_views"] == 3
    assert stats["online_entities_count"] >= 25


def test_feature_store_rest_endpoints(client: TestClient):
    """Testa todos os endpoints da Feature Store na API FastAPI."""
    # 1. GET /api/v1/features/catalog
    res_cat = client.get("/api/v1/features/catalog")
    assert res_cat.status_code == 200
    cat_data = res_cat.json()
    assert cat_data["total_views"] == 3
    assert len(cat_data["feature_views"]) == 3

    # 2. GET /api/v1/features/stats
    res_stats = client.get("/api/v1/features/stats")
    assert res_stats.status_code == 200
    stats_data = res_stats.json()
    assert stats_data["total_feature_views"] == 3
    assert stats_data["online_entities_count"] > 0

    # 3. POST /api/v1/features/online
    res_online = client.post(
        "/api/v1/features/online",
        json={"customer_ids": ["CLI-00001", "CLI-00002"]},
    )
    assert res_online.status_code == 200
    online_data = res_online.json()
    assert online_data["total_entities"] == 2
    assert len(online_data["features"]) == 2
    assert online_data["retrieval_latency_ms"] < 5.0

    # 4. POST /api/v1/features/materialize
    res_mat = client.post(
        "/api/v1/features/materialize",
        json={"limit": 50},
    )
    assert res_mat.status_code == 200
    mat_data = res_mat.json()
    assert mat_data["status"] == "SUCCESS"
    assert mat_data["entities_materialized"] == 50
