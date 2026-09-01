import pytest
from fastapi.testclient import TestClient

from churn_prediction.api.main import app
from churn_prediction.streaming.schemas import (
    BillingEventType,
    BillingPaymentEvent,
    CrmChannel,
    CrmInteractionEvent,
    CrmReason,
    NetworkEventType,
    NetworkTelemetryEvent,
)
from churn_prediction.streaming.window_processor import (
    StreamWindowProcessor,
    window_processor,
)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_window_metrics_calculation():
    """Testa o cálculo preciso das agregações em janelas deslizantes (15m, 1h, 24h, 7d)."""
    proc = StreamWindowProcessor()
    cid = "CLI-WINDOW-001"

    # 1. Envia 2 eventos de rede normais
    evt1 = NetworkTelemetryEvent(
        event_id="net_1",
        customer_id=cid,
        event_type=NetworkEventType.HEARTBEAT,
        download_speed_mbps=100.0,
        upload_speed_mbps=50.0,
        latency_ms=20.0,
        packet_loss_pct=0.2,
        disconnect_count_last_hour=0,
    )
    evt2 = NetworkTelemetryEvent(
        event_id="net_2",
        customer_id=cid,
        event_type=NetworkEventType.HEARTBEAT,
        download_speed_mbps=80.0,
        upload_speed_mbps=40.0,
        latency_ms=30.0,
        packet_loss_pct=0.4,
        disconnect_count_last_hour=0,
    )
    proc.process_event(evt1.model_dump())
    proc.process_event(evt2.model_dump())

    metrics = proc.get_customer_windows(cid)
    assert metrics is not None
    assert metrics.avg_latency_15min == 25.0  # (20 + 30) / 2
    assert metrics.avg_packet_loss_15min == 0.3
    assert metrics.disconnect_count_1h == 0
    assert metrics.realtime_instability_score < 0.30


def test_alert_trigger_on_network_degradation():
    """Testa o disparo de alerta crítico quando ocorrem >= 3 quedas de fibra."""
    proc = StreamWindowProcessor()
    cid = "CLI-ALERT-NET"

    # Envia evento com 3 desconexões
    evt_crit = NetworkTelemetryEvent(
        event_id="net_crit",
        customer_id=cid,
        event_type=NetworkEventType.FIBER_DISCONNECT,
        download_speed_mbps=2.0,
        upload_speed_mbps=0.5,
        latency_ms=250.0,
        packet_loss_pct=25.0,
        disconnect_count_last_hour=3,
    )
    alert = proc.process_event(evt_crit.model_dump())

    assert alert is not None
    assert alert.customer_id == cid
    assert alert.severity == "CRITICA"
    assert "Degradação crítica de rede" in alert.trigger_reason
    assert alert.acknowledged is False

    # Verifica lista de alertas
    active_alerts = proc.get_active_alerts()
    assert len(active_alerts) >= 1
    assert any(a.customer_id == cid for a in active_alerts)

    # Teste de Acknowledge
    ack_res = proc.acknowledge_alert(alert.alert_id, acknowledged_by="analista_suporte")
    assert ack_res is True
    assert alert.acknowledged is True
    assert alert.acknowledged_by == "analista_suporte"


def test_alert_trigger_on_billing_and_crm_insatisfaction():
    """Testa disparo de alerta quando há falha de cobrança combinada com insatisfação no SAC."""
    proc = StreamWindowProcessor()
    cid = "CLI-ALERT-BILL-CRM"

    # Falha de pagamento
    bill_evt = BillingPaymentEvent(
        event_id="bill_fail",
        customer_id=cid,
        event_type=BillingEventType.PAYMENT_FAILED,
        invoice_amount=89.90,
        payment_method="Credit card",
        error_code="ERR_DECLINED",
    )
    proc.process_event(bill_evt.model_dump())

    # Chamada com sentimento muito negativo
    crm_evt = CrmInteractionEvent(
        event_id="crm_angry",
        customer_id=cid,
        channel=CrmChannel.CALL_CENTER,
        reason=CrmReason.CONTESTACAO_FATURA,
        sentiment_score=-0.80,
        duration_seconds=420,
    )
    alert = proc.process_event(crm_evt.model_dump())

    assert alert is not None
    assert alert.customer_id == cid
    assert alert.severity == "ALTA"
    assert "Risco financeiro com insatisfação" in alert.trigger_reason


def test_rest_api_windows_and_alerts_endpoints(client: TestClient):
    """Testa os endpoints da API para consulta de janelas e alertas."""
    cid = "CLI-API-TEST"
    # Popula evento no window_processor global
    net_evt = NetworkTelemetryEvent(
        event_id="evt_api_01",
        customer_id=cid,
        event_type=NetworkEventType.FIBER_DISCONNECT,
        download_speed_mbps=1.0,
        upload_speed_mbps=0.2,
        latency_ms=300.0,
        packet_loss_pct=30.0,
        disconnect_count_last_hour=4,
    )
    window_processor.process_event(net_evt.model_dump())

    # 1. GET /api/v1/streaming/windows
    res_windows = client.get("/api/v1/streaming/windows")
    assert res_windows.status_code == 200
    data_windows = res_windows.json()
    assert "total_customers_tracked" in data_windows
    assert data_windows["total_customers_tracked"] >= 1

    # 2. GET /api/v1/streaming/windows/{customer_id}
    res_single = client.get(f"/api/v1/streaming/windows/{cid}")
    assert res_single.status_code == 200
    single_data = res_single.json()
    assert single_data["customer_id"] == cid
    assert single_data["disconnect_count_1h"] == 4

    # Teste 404
    res_404 = client.get("/api/v1/streaming/windows/INEXISTENTE-999")
    assert res_404.status_code == 404

    # 3. GET /api/v1/streaming/alerts
    res_alerts = client.get("/api/v1/streaming/alerts")
    assert res_alerts.status_code == 200
    alerts_data = res_alerts.json()
    assert alerts_data["total_alerts"] >= 1
    target_alert = next((a for a in alerts_data["alerts"] if a["customer_id"] == cid), None)
    assert target_alert is not None
    alert_id = target_alert["alert_id"]

    # 4. POST /api/v1/streaming/alerts/{alert_id}/acknowledge
    res_ack = client.post(
        f"/api/v1/streaming/alerts/{alert_id}/acknowledge",
        json={"acknowledged_by": "sistema_retencao_auto"},
    )
    assert res_ack.status_code == 200
    assert res_ack.json()["success"] is True

    # Teste 404 no Acknowledge
    res_ack_404 = client.post(
        "/api/v1/streaming/alerts/alt_nao_existe/acknowledge",
        json={"acknowledged_by": "operador"},
    )
    assert res_ack_404.status_code == 404
