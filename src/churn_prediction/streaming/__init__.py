"""Subsistema de Streaming, Processamento em Tempo Real & Event Generation (Fase 2 - Marcos M11/M12)."""

from churn_prediction.streaming.consumer import (
    StreamingKafkaConsumerWorker,
    consumer_worker,
)
from churn_prediction.streaming.generator import (
    CustomerProfile,
    StreamingEventGenerator,
    generator_instance,
)
from churn_prediction.streaming.producer import (
    StreamingProducerRouter,
    producer_router,
)
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
from churn_prediction.streaming.window_processor import (
    CustomerWindowMetrics,
    RealtimeRiskAlert,
    StreamWindowProcessor,
    window_processor,
)

__all__ = [
    "AnyStreamingEvent",
    "BillingEventType",
    "BillingPaymentEvent",
    "CrmChannel",
    "CrmInteractionEvent",
    "CrmReason",
    "CustomerProfile",
    "CustomerWindowMetrics",
    "NetworkEventType",
    "NetworkTelemetryEvent",
    "RealtimeRiskAlert",
    "StreamWindowProcessor",
    "StreamingEventGenerator",
    "StreamingKafkaConsumerWorker",
    "StreamingProducerRouter",
    "consumer_worker",
    "generator_instance",
    "producer_router",
    "window_processor",
]
