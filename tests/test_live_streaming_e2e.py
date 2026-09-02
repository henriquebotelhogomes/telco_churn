import pytest
from starlette.testclient import TestClient

from churn_prediction.api.main import app
from churn_prediction.features.live_scorer import live_scorer
from churn_prediction.streaming.broadcaster import LiveEventMessage, sse_broadcaster
from churn_prediction.streaming.window_processor import window_processor


@pytest.fixture
def client():
    return TestClient(app)


def test_sse_broadcaster_publish_and_tenant_filtering():
    """Testa o hub SSE assíncrono e isolamento multi-tenant de eventos."""
    queue_global = sse_broadcaster.subscribe("tenant-default")
    queue_vivo = sse_broadcaster.subscribe("tenant-vivo")
    queue_claro = sse_broadcaster.subscribe("tenant-claro")

    try:
        # Evento específico da Vivo
        msg_vivo = LiveEventMessage(
            event_type="TELEMETRY",
            tenant_id="tenant-vivo",
            customer_id="5575-GNVDE",
            data={"latency": 150.0},
        )
        sse_broadcaster.publish(msg_vivo)

        # Global e Vivo devem receber; Claro não deve
        assert not queue_global.empty()
        assert not queue_vivo.empty()
        assert queue_claro.empty()

        received_vivo = queue_vivo.get_nowait()
        assert received_vivo.customer_id == "5575-GNVDE"
        assert received_vivo.tenant_id == "tenant-vivo"

        received_global = queue_global.get_nowait()
        assert received_global.customer_id == "5575-GNVDE"

    finally:
        sse_broadcaster.unsubscribe(queue_global, "tenant-default")
        sse_broadcaster.unsubscribe(queue_vivo, "tenant-vivo")
        sse_broadcaster.unsubscribe(queue_claro, "tenant-claro")


def test_live_scorer_re_score_with_instability():
    """Testa reavaliação de churn em tempo real quando ocorrem falhas de rede."""
    cid = "7590-VHVEG"
    tid = "tenant-tim"

    # Baseline inicial
    initial_score = live_scorer.re_score_customer(cid, tid)
    assert 0.0 <= initial_score.new_risk_score <= 1.0

    # Injeta eventos caóticos de rede nas janelas do Flink
    for _ in range(4):
        window_processor.process_event({
            "event_type": "FIBER_DISCONNECT",
            "topic": "telemetry.network.events",
            "tenant_id": tid,
            "customer_id": cid,
            "latency_ms": 190.0,
            "packet_loss_pct": 12.0,
            "disconnect_count_last_hour": 3,
        })

    # Reavalia o score após as quedas
    updated_score = live_scorer.re_score_customer(cid, tid)
    assert updated_score.new_risk_score >= initial_score.previous_risk_score
    assert len(updated_score.reasons) > 0
    assert updated_score.risk_level in ["Médio", "Alto", "Crítico"]


def test_streaming_chaos_scenarios_and_live_scores_api(client: TestClient):
    """Testa endpoints REST de injeção de caos e consulta de live scores."""
    # 1. Injetar Rompimento de Fibra
    res_fiber = client.post("/api/v1/streaming/chaos/scenarios/fiber_cut")
    assert res_fiber.status_code == 200
    assert res_fiber.json()["scenario_id"] == "fiber_cut"

    # 2. Injetar Falha no Gateway PIX
    res_pay = client.post("/api/v1/streaming/chaos/scenarios/payment_gateway_down")
    assert res_pay.status_code == 200
    assert res_pay.json()["scenario_id"] == "payment_gateway_down"

    # 3. Injetar Crise no Atendimento CRM
    res_crm = client.post("/api/v1/streaming/chaos/scenarios/crm_crisis")
    assert res_crm.status_code == 200
    assert res_crm.json()["scenario_id"] == "crm_crisis"

    # 4. Consultar Live Scores via REST
    res_scores = client.get("/api/v1/streaming/live-scores?tenant_id=tenant-default")
    assert res_scores.status_code == 200
    data = res_scores.json()
    assert "total_customers" in data
    assert "scores" in data
    assert len(data["scores"]) > 0
