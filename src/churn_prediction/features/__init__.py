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
    "UnifiedFeatureStore",
    "feature_store",
]
