import pytest
from pydantic import ValidationError

from churn_prediction.streaming.schemas import (
    BillingEventType,
    BillingPaymentEvent,
    CrmChannel,
    CrmInteractionEvent,
    CrmReason,
    NetworkEventType,
    NetworkTelemetryEvent,
)


def test_network_telemetry_event_valid():
    evt = NetworkTelemetryEvent(
        event_id="evt_net_001",
        customer_id="VIVO-5575",
        tenant_id="telecom_sp",
        event_type=NetworkEventType.FIBER_DISCONNECT,
        download_speed_mbps=1.5,
        upload_speed_mbps=0.3,
        latency_ms=185.4,
        packet_loss_pct=14.2,
        disconnect_count_last_hour=3,
    )
    assert evt.topic == "telemetry.network.events"
    assert evt.customer_id == "VIVO-5575"
    assert evt.tenant_id == "telecom_sp"
    assert evt.latency_ms == 185.4


def test_network_telemetry_event_invalid_packet_loss():
    with pytest.raises(ValidationError):
        NetworkTelemetryEvent(
            event_id="evt_net_invalid",
            customer_id="VIVO-5575",
            event_type=NetworkEventType.LATENCY_SPIKE,
            download_speed_mbps=10.0,
            upload_speed_mbps=5.0,
            latency_ms=50.0,
            packet_loss_pct=150.0,  # Max 100.0%
        )


def test_billing_payment_event_valid():
    evt = BillingPaymentEvent(
        event_id="evt_bill_001",
        customer_id="CLARO-8812",
        tenant_id="telecom_sp",
        event_type=BillingEventType.PAYMENT_FAILED,
        invoice_amount=4250.0,
        payment_method="PIX",
        error_code="INSUFFICIENT_FUNDS",
        error_reason="Saldo insuficiente no gateway",
    )
    assert evt.topic == "billing.payment.events"
    assert evt.invoice_amount == 4250.0


def test_crm_interaction_event_valid():
    evt = CrmInteractionEvent(
        event_id="evt_crm_001",
        customer_id="TIM-3301",
        tenant_id="telecom_sp",
        channel=CrmChannel.WHATSAPP,
        reason=CrmReason.LENTIDAO_INTERNET,
        sentiment_score=-0.85,
        duration_seconds=120,
    )
    assert evt.topic == "crm.interaction.events"
    assert evt.sentiment_score == -0.85


def test_crm_interaction_event_invalid_sentiment():
    with pytest.raises(ValidationError):
        CrmInteractionEvent(
            event_id="evt_crm_invalid",
            customer_id="TIM-3301",
            channel=CrmChannel.WHATSAPP,
            reason=CrmReason.LENTIDAO_INTERNET,
            sentiment_score=2.5,  # Valid range is -1.0 to 1.0
            duration_seconds=60,
        )
