"""Subsistema de Multi-Tenancy Estrito & Row-Level Security (Fase 2 - Marco M14)."""

from churn_prediction.tenancy.context import (
    TenantContextMiddleware,
    get_current_tenant,
    get_current_tenant_id,
    set_current_tenant_id,
)
from churn_prediction.tenancy.manager import (
    TenantInfo,
    TenantManager,
    tenant_manager,
)

__all__ = [
    "TenantContextMiddleware",
    "TenantInfo",
    "TenantManager",
    "get_current_tenant",
    "get_current_tenant_id",
    "set_current_tenant_id",
    "tenant_manager",
]
