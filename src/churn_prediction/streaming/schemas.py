from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class NetworkEventType(StrEnum):
    HEARTBEAT = "HEARTBEAT"
    LATENCY_SPIKE = "LATENCY_SPIKE"
    PACKET_LOSS_SPIKE = "PACKET_LOSS_SPIKE"
    FIBER_DISCONNECT = "FIBER_DISCONNECT"
    SIGNAL_DEGRADATION = "SIGNAL_DEGRADATION"


class BillingEventType(StrEnum):
    INVOICE_GENERATED = "INVOICE_GENERATED"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    CARD_EXPIRED = "CARD_EXPIRED"
    PAYMENT_METHOD_CHANGED = "PAYMENT_METHOD_CHANGED"


class CrmChannel(StrEnum):
    CALL_CENTER = "CALL_CENTER"
    WHATSAPP = "WHATSAPP"
    MOBILE_APP = "MOBILE_APP"
    WEB_PORTAL = "WEB_PORTAL"


class CrmReason(StrEnum):
    CONTESTACAO_FATURA = "CONTESTACAO_FATURA"
    LENTIDAO_INTERNET = "LENTIDAO_INTERNET"
    CANCELAMENTO_SOLICITADO = "CANCELAMENTO_SOLICITADO"
    DUVIDA_PLANO = "DUVIDA_PLANO"
    ELOGIO = "ELOGIO"


class BaseStreamingEvent(BaseModel):
    """Esquema base para todos os eventos em streaming."""
    event_id: str = Field(..., description="Identificador único do evento")
    customer_id: str = Field(..., description="ID do cliente")
    tenant_id: str = Field(default="tenant-default", description="Identificador multi-tenant")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="Timestamp UTC no padrão ISO 8601"
    )


class NetworkTelemetryEvent(BaseStreamingEvent):
    """Evento emitido por roteadores, modems e antenas 4G/5G/Fibra."""
    topic: str = "telemetry.network.events"
    event_type: NetworkEventType = Field(..., description="Tipo de ocorrência de rede")
    download_speed_mbps: float = Field(..., ge=0.0, description="Velocidade de download (Mbps)")
    upload_speed_mbps: float = Field(..., ge=0.0, description="Velocidade de upload (Mbps)")
    latency_ms: float = Field(..., ge=0.0, description="Latência média de ping (ms)")
    packet_loss_pct: float = Field(..., ge=0.0, le=100.0, description="Porcentagem de pacotes perdidos")
    disconnect_count_last_hour: int = Field(default=0, ge=0, description="Quedas de sinal na última hora")


class BillingPaymentEvent(BaseStreamingEvent):
    """Evento emitido pelo gateway de pagamento e faturamento."""
    topic: str = "billing.payment.events"
    event_type: BillingEventType = Field(..., description="Tipo de transação financeira")
    invoice_amount: float = Field(..., ge=0.0, description="Valor da fatura em BRL")
    attempt_number: int = Field(default=1, ge=1, description="Tentativa de cobrança")
    payment_method: str = Field(..., description="Forma de pagamento")
    error_code: str | None = Field(default=None, description="Código de erro se houver falha")
    error_reason: str | None = Field(default=None, description="Descrição amigável da falha")


class CrmInteractionEvent(BaseStreamingEvent):
    """Evento emitido pela central de atendimento e canais digitais."""
    topic: str = "crm.interaction.events"
    channel: CrmChannel = Field(..., description="Canal de atendimento")
    reason: CrmReason = Field(..., description="Motivo do contato")
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Score de sentimento (-1.0 a +1.0)")
    duration_seconds: int = Field(..., ge=0, description="Duração do contato em segundos")
    agent_id: str = Field(default="bot-agent-01", description="Identificador do agente/bot")
    notes: str | None = Field(default=None, description="Observações do atendimento")


type AnyStreamingEvent = NetworkTelemetryEvent | BillingPaymentEvent | CrmInteractionEvent
