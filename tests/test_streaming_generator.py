import pytest
from fastapi.testclient import TestClient

from churn_prediction.api.main import app
from churn_prediction.streaming.generator import (
    CustomerProfile,
    StreamingEventGenerator,
    generator_instance,
)
from churn_prediction.streaming.producer import producer_router
from churn_prediction.streaming.schemas import (
    BillingEventType,
    BillingPaymentEvent,
    CrmInteractionEvent,
    NetworkTelemetryEvent,
)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_schema_validations():
    """Valida a criação e restrições dos esquemas de streaming."""
    net_evt = NetworkTelemetryEvent(
        event_id="evt_01",
        customer_id="CLI-001",
        download_speed_mbps=150.0,
        upload_speed_mbps=80.0,
        latency_ms=12.5,
        packet_loss_pct=0.1,
        event_type="HEARTBEAT",
    )
    assert net_evt.topic == "telemetry.network.events"
    assert net_evt.download_speed_mbps == 150.0

    bill_evt = BillingPaymentEvent(
        event_id="evt_02",
        customer_id="CLI-002",
        invoice_amount=89.90,
        payment_method="Credit card",
        event_type=BillingEventType.PAYMENT_SUCCESS,
    )
    assert bill_evt.topic == "billing.payment.events"
    assert bill_evt.invoice_amount == 89.90

    crm_evt = CrmInteractionEvent(
        event_id="evt_03",
        customer_id="CLI-003",
        channel="CALL_CENTER",
        reason="LENTIDAO_INTERNET",
        sentiment_score=-0.75,
        duration_seconds=180,
    )
    assert crm_evt.topic == "crm.interaction.events"
    assert crm_evt.sentiment_score == -0.75


def test_generator_event_profiles():
    """Testa geração de eventos sob diferentes perfis de cliente."""
    gen = StreamingEventGenerator()

    # Saudável
    evt_healthy = gen.generate_single_event("CLI-HEALTHY", profile=CustomerProfile.HEALTHY)
    assert evt_healthy.customer_id == "CLI-HEALTHY"

    # Crítico
    evt_critical = gen.generate_single_event("CLI-CRITICAL", profile=CustomerProfile.CRITICAL)
    assert evt_critical.customer_id == "CLI-CRITICAL"


def test_producer_router_fallback():
    """Testa se o producer router roteia com segurança para o buffer in-memory."""
    import asyncio

    net_evt = NetworkTelemetryEvent(
        event_id="evt_test",
        customer_id="CLI-PROD",
        download_speed_mbps=100.0,
        upload_speed_mbps=50.0,
        latency_ms=15.0,
        packet_loss_pct=0.0,
        event_type="HEARTBEAT",
    )
    success = asyncio.run(producer_router.publish_event(net_evt))
    assert success is True
    assert len(generator_instance.recent_events) > 0


def test_streaming_api_endpoints(client: TestClient):
    """Testa os endpoints REST de controle de streaming."""
    # 1. Status inicial
    res = client.get("/api/v1/streaming/status")
    assert res.status_code == 200
    data = res.json()
    assert "is_running" in data
    assert "total_generated" in data

    # 2. Iniciar streaming
    res_start = client.post("/api/v1/streaming/start", json={"events_per_second": 10.0})
    assert res_start.status_code == 200
    assert res_start.json()["is_running"] is True
    assert res_start.json()["events_per_second"] == 10.0

    # 3. Injetar Caos
    res_chaos = client.post("/api/v1/streaming/chaos/inject", json={"enable_chaos": True})
    assert res_chaos.status_code == 200
    assert res_chaos.json()["chaos_mode"] is True

    # 4. Parar streaming
    res_stop = client.post("/api/v1/streaming/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["is_running"] is False
