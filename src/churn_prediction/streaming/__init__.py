"""Subsistema de Streaming & Event Generation (Fase 2 - Marco M11)."""

from churn_prediction.streaming.generator import (
    CustomerProfile,
    StreamingEventGenerator,
    generator_instance,
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

__all__ = [
    "AnyStreamingEvent",
    "BillingEventType",
    "BillingPaymentEvent",
    "CrmChannel",
    "CrmInteractionEvent",
    "CrmReason",
    "CustomerProfile",
    "NetworkEventType",
    "NetworkTelemetryEvent",
    "StreamingEventGenerator",
    "generator_instance",
]
