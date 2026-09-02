import datetime
from typing import Any

from pydantic import BaseModel, Field


class TenantInfo(BaseModel):
    """Metadados e limites de uma operadora (tenant)."""

    tenant_id: str = Field(..., description="Identificador único (ex: tenant-vivo)")
    name: str = Field(..., description="Nome corporativo da operadora")
    plan: str = Field(
        default="ENTERPRISE", description="Plano contratual (STANDARD | ENTERPRISE | DEDICATED)"
    )
    rate_limit_rps: int = Field(default=200, description="Limite de requisições por segundo")
    status: str = Field(default="ACTIVE", description="ACTIVE | SUSPENDED | PROVISIONING")
    created_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())
    custom_model_enabled: bool = Field(
        default=False, description="Se possui modelo de ML customizado"
    )


class TenantManager:
    """Gerenciador centralizado de operadoras/tenants da plataforma B2B SaaS."""

    def __init__(self):
        self._tenants: dict[str, TenantInfo] = {}
        self._init_default_tenants()

    def _init_default_tenants(self) -> None:
        """Inicializa os tenants padrão de telecomunicações."""
        defaults = [
            TenantInfo(
                tenant_id="tenant-default",
                name="RetainIQ Global",
                plan="DEDICATED",
                rate_limit_rps=500,
                status="ACTIVE",
                custom_model_enabled=True,
            ),
            TenantInfo(
                tenant_id="tenant-vivo",
                name="Vivo Telecom B2B",
                plan="ENTERPRISE",
                rate_limit_rps=300,
                status="ACTIVE",
                custom_model_enabled=True,
            ),
            TenantInfo(
                tenant_id="tenant-claro",
                name="Claro Brasil",
                plan="ENTERPRISE",
                rate_limit_rps=300,
                status="ACTIVE",
                custom_model_enabled=False,
            ),
            TenantInfo(
                tenant_id="tenant-tim",
                name="TIM Celular",
                plan="STANDARD",
                rate_limit_rps=150,
                status="ACTIVE",
                custom_model_enabled=False,
            ),
        ]
        for t in defaults:
            self._tenants[t.tenant_id] = t

    def list_tenants(self) -> list[TenantInfo]:
        """Retorna a lista de todos os tenants cadastrados."""
        return list(self._tenants.values())

    def get_tenant(self, tenant_id: str) -> TenantInfo | None:
        """Busca um tenant pelo identificador."""
        return self._tenants.get(tenant_id)

    def create_tenant(
        self,
        tenant_id: str,
        name: str,
        plan: str = "ENTERPRISE",
        rate_limit_rps: int = 200,
        custom_model_enabled: bool = False,
    ) -> TenantInfo:
        """Provisiona um novo tenant na plataforma."""
        clean_id = tenant_id.strip().lower()
        if not clean_id.startswith("tenant-"):
            clean_id = f"tenant-{clean_id}"

        tenant = TenantInfo(
            tenant_id=clean_id,
            name=name.strip(),
            plan=plan,
            rate_limit_rps=rate_limit_rps,
            status="ACTIVE",
            custom_model_enabled=custom_model_enabled,
        )
        self._tenants[clean_id] = tenant
        return tenant

    def get_tenant_summary(self, tenant_id: str) -> dict[str, Any]:
        """Retorna o resumo consolidado de operação e volumetria do tenant."""
        tenant = self.get_tenant(tenant_id)
        if tenant is None:
            tenant = self.create_tenant(tenant_id, name=f"Operadora {tenant_id}")

        return {
            "tenant_id": tenant.tenant_id,
            "name": tenant.name,
            "plan": tenant.plan,
            "status": tenant.status,
            "rate_limit_rps": tenant.rate_limit_rps,
            "custom_model_enabled": tenant.custom_model_enabled,
            "active_customers_count": 1250,
            "high_risk_customers_count": 184,
            "monthly_retention_roi_brl": 42500.0,
            "data_isolation_level": "STRICT_ROW_LEVEL_SECURITY",
        }


# Instância Singleton do Gerenciador de Tenants
tenant_manager = TenantManager()
