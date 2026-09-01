import pytest
from fastapi.testclient import TestClient

from churn_prediction.api.main import app
from churn_prediction.tenancy.context import (
    get_current_tenant_id,
    set_current_tenant_id,
)
from churn_prediction.tenancy.manager import TenantManager


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_tenant_context_management():
    """Testa a definição e recuperação do tenant no contexto assíncrono."""
    set_current_tenant_id("tenant-vivo")
    assert get_current_tenant_id() == "tenant-vivo"

    set_current_tenant_id("")
    assert get_current_tenant_id() == "tenant-default"


def test_tenant_manager_lifecycle():
    """Testa provisionamento e catálogo de tenants."""
    mgr = TenantManager()
    tenants = mgr.list_tenants()
    assert len(tenants) >= 4

    tenant_ids = [t.tenant_id for t in tenants]
    assert "tenant-default" in tenant_ids
    assert "tenant-vivo" in tenant_ids
    assert "tenant-claro" in tenant_ids
    assert "tenant-tim" in tenant_ids

    # Provisiona novo tenant
    new_t = mgr.create_tenant(
        tenant_id="algar",
        name="Algar Telecom",
        plan="ENTERPRISE",
        rate_limit_rps=250,
    )
    assert new_t.tenant_id == "tenant-algar"
    assert new_t.name == "Algar Telecom"
    assert mgr.get_tenant("tenant-algar") is not None

    # Resumo
    summary = mgr.get_tenant_summary("tenant-algar")
    assert summary["tenant_id"] == "tenant-algar"
    assert summary["data_isolation_level"] == "STRICT_ROW_LEVEL_SECURITY"


def test_tenant_rest_endpoints(client: TestClient):
    """Testa os endpoints da API para listagem, provisionamento e resumo de tenants."""
    # 1. GET /api/v1/tenants
    res_list = client.get("/api/v1/tenants")
    assert res_list.status_code == 200
    data_list = res_list.json()
    assert data_list["total_tenants"] >= 4

    # 2. POST /api/v1/tenants (provisionamento)
    res_prov = client.post(
        "/api/v1/tenants",
        json={
            "tenant_id": "tenant-oi",
            "name": "Oi Soluções",
            "plan": "ENTERPRISE",
            "rate_limit_rps": 180,
            "custom_model_enabled": True,
        },
    )
    assert res_prov.status_code == 200
    prov_data = res_prov.json()
    assert prov_data["tenant_id"] == "tenant-oi"
    assert prov_data["custom_model_enabled"] is True

    # 3. GET /api/v1/tenants/tenant-oi/summary
    res_sum = client.get("/api/v1/tenants/tenant-oi/summary")
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    assert sum_data["tenant_id"] == "tenant-oi"
    assert sum_data["data_isolation_level"] == "STRICT_ROW_LEVEL_SECURITY"

    # 4. Verifica injeção do header X-Tenant-ID na resposta pelo Middleware
    res_head = client.get(
        "/api/v1/tenants",
        headers={"X-Tenant-ID": "tenant-claro"},
    )
    assert res_head.status_code == 200
    assert res_head.headers.get("X-Tenant-ID") == "tenant-claro"
