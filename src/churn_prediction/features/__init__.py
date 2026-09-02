"""Subsistema de Feature Store Unificada em Tempo Real (Fase 2 - Marco M13)."""

from churn_prediction.features.definitions import (
    ALL_FEATURE_VIEWS,
    CUSTOMER_DEMOGRAPHIC_FV,
    CUSTOMER_FINANCIAL_FV,
    CUSTOMER_REALTIME_STREAM_FV,
    FeatureField,
    FeatureSourceType,
    FeatureType,
    FeatureViewMetadata,
)
from churn_prediction.features.live_scorer import (
    LiveCustomerScoreUpdate,
    LiveScorerEngine,
    live_scorer,
)
from churn_prediction.features.store import (
    UnifiedFeatureStore,
    feature_store,
)

__all__ = [
    "ALL_FEATURE_VIEWS",
    "CUSTOMER_DEMOGRAPHIC_FV",
    "CUSTOMER_FINANCIAL_FV",
    "CUSTOMER_REALTIME_STREAM_FV",
    "FeatureField",
    "FeatureSourceType",
    "FeatureType",
    "FeatureViewMetadata",
    "LiveCustomerScoreUpdate",
    "LiveScorerEngine",
    "UnifiedFeatureStore",
    "feature_store",
    "live_scorer",
]
