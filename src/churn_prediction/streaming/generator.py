import asyncio
import random
import uuid
from collections import deque
from datetime import UTC, datetime
from typing import Any

from churn_prediction.streaming.schemas import (
    AnyStreamingEvent,
    BillingEventType,
    BillingPaymentEvent,
    CrmChannel,
    CrmInteractionEvent,
    CrmReason,
    NetworkEventType,
    NetworkTelemetryEvent,
)


class CustomerProfile:
    HEALTHY = "HEALTHY"
    DEGRADING = "DEGRADING"
    CRITICAL = "CRITICAL"


class StreamingEventGenerator:
    """Motor assíncrono de simulação estocástica para geração contínua de eventos em streaming."""

    def __init__(self, buffer_maxlen: int = 5000):
        self.is_running: bool = False
        self.events_per_second: float = 5.0
        self.chaos_mode: bool = False
        self.recent_events: deque[dict[str, Any]] = deque(maxlen=buffer_maxlen)
        self._task: asyncio.Task[None] | None = None
        self.total_generated: dict[str, int] = {
            "telemetry.network.events": 0,
            "billing.payment.events": 0,
            "crm.interaction.events": 0,
        }

    def generate_single_event(
        self,
        customer_id: str,
        profile: str = CustomerProfile.HEALTHY,
        tenant_id: str = "tenant-default",
    ) -> AnyStreamingEvent:
        """Gera um evento tipado e contextual com base no perfil comportamental do cliente."""
        event_choice = random.choices(["network", "billing", "crm"], weights=[0.70, 0.15, 0.15])[0]
        now_iso = datetime.now(UTC).isoformat()
        evt_id = f"evt_{uuid.uuid4().hex[:10]}"

        if event_choice == "network":
            if self.chaos_mode or profile == CustomerProfile.CRITICAL:
                return NetworkTelemetryEvent(
                    event_id=evt_id,
                    customer_id=customer_id,
                    tenant_id=tenant_id,
                    timestamp=now_iso,
                    event_type=NetworkEventType.FIBER_DISCONNECT,
                    download_speed_mbps=round(random.uniform(0.5, 5.0), 1),
                    upload_speed_mbps=round(random.uniform(0.1, 1.0), 1),
                    latency_ms=round(random.uniform(150.0, 450.0), 1),
                    packet_loss_pct=round(random.uniform(15.0, 45.0), 1),
                    disconnect_count_last_hour=random.randint(3, 10),
                )
            elif profile == CustomerProfile.DEGRADING:
                return NetworkTelemetryEvent(
                    event_id=evt_id,
                    customer_id=customer_id,
                    tenant_id=tenant_id,
                    timestamp=now_iso,
                    event_type=NetworkEventType.LATENCY_SPIKE,
                    download_speed_mbps=round(random.uniform(15.0, 40.0), 1),
                    upload_speed_mbps=round(random.uniform(5.0, 15.0), 1),
                    latency_ms=round(random.uniform(60.0, 140.0), 1),
                    packet_loss_pct=round(random.uniform(2.0, 8.0), 1),
                    disconnect_count_last_hour=random.randint(1, 2),
                )
            else:
                return NetworkTelemetryEvent(
                    event_id=evt_id,
                    customer_id=customer_id,
                    tenant_id=tenant_id,
                    timestamp=now_iso,
                    event_type=NetworkEventType.HEARTBEAT,
                    download_speed_mbps=round(random.uniform(80.0, 300.0), 1),
                    upload_speed_mbps=round(random.uniform(40.0, 150.0), 1),
                    latency_ms=round(random.uniform(8.0, 25.0), 1),
                    packet_loss_pct=round(random.uniform(0.0, 0.5), 1),
                    disconnect_count_last_hour=0,
                )

        elif event_choice == "billing":
            if self.chaos_mode or profile == CustomerProfile.CRITICAL:
                return BillingPaymentEvent(
                    event_id=evt_id,
                    customer_id=customer_id,
                    tenant_id=tenant_id,
                    timestamp=now_iso,
                    event_type=BillingEventType.PAYMENT_FAILED,
                    invoice_amount=round(random.uniform(65.0, 140.0), 2),
                    attempt_number=random.randint(2, 4),
                    payment_method="Credit card (automatic)",
                    error_code="ERR_CARD_EXPIRED_OR_DECLINED",
                    error_reason="Transação negada pelo emissor do cartão",
                )
            else:
                return BillingPaymentEvent(
                    event_id=evt_id,
                    customer_id=customer_id,
                    tenant_id=tenant_id,
                    timestamp=now_iso,
                    event_type=BillingEventType.PAYMENT_SUCCESS,
                    invoice_amount=round(random.uniform(50.0, 120.0), 2),
                    attempt_number=1,
                    payment_method="Bank transfer (automatic)",
                )

        else:  # crm
            if self.chaos_mode or profile == CustomerProfile.CRITICAL:
                return CrmInteractionEvent(
                    event_id=evt_id,
                    customer_id=customer_id,
                    tenant_id=tenant_id,
                    timestamp=now_iso,
                    channel=CrmChannel.CALL_CENTER,
                    reason=CrmReason.CANCELAMENTO_SOLICITADO,
                    sentiment_score=round(random.uniform(-0.95, -0.60), 2),
                    duration_seconds=random.randint(300, 900),
                    notes="Cliente insatisfeito com instabilidades recorrentes.",
                )
            elif profile == CustomerProfile.DEGRADING:
                return CrmInteractionEvent(
                    event_id=evt_id,
                    customer_id=customer_id,
                    tenant_id=tenant_id,
                    timestamp=now_iso,
                    channel=CrmChannel.WHATSAPP,
                    reason=CrmReason.LENTIDAO_INTERNET,
                    sentiment_score=round(random.uniform(-0.55, -0.10), 2),
                    duration_seconds=random.randint(120, 360),
                )
            else:
                return CrmInteractionEvent(
                    event_id=evt_id,
                    customer_id=customer_id,
                    tenant_id=tenant_id,
                    timestamp=now_iso,
                    channel=CrmChannel.MOBILE_APP,
                    reason=CrmReason.DUVIDA_PLANO,
                    sentiment_score=round(random.uniform(0.30, 0.90), 2),
                    duration_seconds=random.randint(30, 120),
                )

    async def _run_loop(self) -> None:
        """Loop contínuo de geração assíncrona."""
        sample_customers = [f"CLI-{i:05d}" for i in range(1, 1001)]
        while self.is_running:
            delay = 1.0 / max(self.events_per_second, 0.1)
            cid = random.choice(sample_customers)
            profile = random.choices(
                [CustomerProfile.HEALTHY, CustomerProfile.DEGRADING, CustomerProfile.CRITICAL],
                weights=[0.80, 0.15, 0.05],
            )[0]

            event = self.generate_single_event(cid, profile=profile)
            evt_dict = event.model_dump()
            self.recent_events.append(evt_dict)
            self.total_generated[event.topic] = self.total_generated.get(event.topic, 0) + 1

            await asyncio.sleep(delay)

    def start(self, events_per_second: float = 5.0) -> None:
        """Inicia a geração contínua em background."""
        if not self.is_running:
            self.is_running = True
            self.events_per_second = max(0.5, min(events_per_second, 500.0))
            try:
                loop = asyncio.get_running_loop()
                self._task = loop.create_task(self._run_loop())
            except RuntimeError:
                # Caso o ambiente seja síncrono sem loop ativo (ex: testes síncronos)
                pass

    def stop(self) -> None:
        """Pausa a geração de eventos."""
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()

    def get_status(self) -> dict[str, Any]:
        """Retorna as métricas de telemetria e o estado do gerador."""
        return {
            "is_running": self.is_running,
            "events_per_second": self.events_per_second,
            "chaos_mode": self.chaos_mode,
            "buffer_size": len(self.recent_events),
            "total_generated": self.total_generated,
            "recent_events": list(self.recent_events)[-10:],
        }


# Instância Singleton
generator_instance = StreamingEventGenerator()
