import pytest
from fastapi.testclient import TestClient

from churn_prediction.api.main import app

client = TestClient(app)


def test_apply_playbook_and_history():
    """Testa aplicação de playbook e consulta ao histórico (RetainIQ M6)."""
    with TestClient(app) as live_client:
        payload = {
            "customer_id": "TEST-CUST-101",
            "playbook": "MIGRAÇÃO_CONTRATO_ANUAL",
            "discount_pct": 15.0,
            "estimated_risk_reduction": 0.35,
            "expected_annual_savings": 450.0,
            "description": "Desconto de 15% para contrato de 1 ano",
            "applied_by": "analyst_test",
            "notes": "Cliente aceitou a proposta na primeira ligação",
        }
        res = live_client.post("/api/v1/playbooks/apply", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["customer_id"] == "TEST-CUST-101"
        assert data["playbook"] == "MIGRAÇÃO_CONTRATO_ANUAL"
        assert data["status"] == "applied"
        assert "applied_at" in data

        # Consulta histórico por cliente
        hist_res = live_client.get("/api/v1/playbooks/history?customer_id=TEST-CUST-101")
        assert hist_res.status_code == 200
        hist_data = hist_res.json()
        assert len(hist_data) >= 1
        assert hist_data[0]["customer_id"] == "TEST-CUST-101"
        assert hist_data[0]["applied_by"] == "analyst_test"


def test_record_outcome():
    """Testa registro de desfecho real de churn/retenção (M6)."""
    with TestClient(app) as live_client:
        payload = {
            "customer_id": "TEST-CUST-101",
            "churn_occurred": 0,
            "observed_months": 3,
            "actual_revenue_saved": 450.0,
            "notes": "Cliente permaneceu ativo após 3 meses da ação",
        }
        res = live_client.post("/api/v1/outcomes/record", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["customer_id"] == "TEST-CUST-101"
        assert data["churn_occurred"] == 0
        assert "outcome_date" in data


def test_analytics_temporal_evolution():
    """Testa endpoint analítico de evolução temporal (M6)."""
    with TestClient(app) as live_client:
        res = live_client.get("/api/v1/analytics/temporal-evolution")
        assert res.status_code == 200
        data = res.json()
        assert "pontos" in data
        assert "resumo_global" in data
        assert isinstance(data["pontos"], list)
        if len(data["pontos"]) > 0:
            primeiro = data["pontos"][0]
            assert "periodo" in primeiro
            assert "total_analisado" in primeiro
            assert "taxa_retencao_pct" in primeiro


def test_analytics_retention_efficiency():
    """Testa endpoint de eficiência de retenção por playbook (M6)."""
    with TestClient(app) as live_client:
        res = live_client.get("/api/v1/analytics/retention-efficiency")
        assert res.status_code == 200
        data = res.json()
        assert "taxa_global_eficiencia_pct" in data
        assert "detalhe_por_playbook" in data
        assert isinstance(data["detalhe_por_playbook"], list)
        if len(data["detalhe_por_playbook"]) > 0:
            pb = data["detalhe_por_playbook"][0]
            assert "playbook" in pb
            assert "taxa_sucesso_pct" in pb
            assert "total_aplicado" in pb


@pytest.mark.anyio
async def test_seed_historical_data_execution():
    """Testa a execução do seed com force=True."""
    from churn_prediction.db.seed import seed_historical_data

    res = await seed_historical_data(force=True)
    assert res["status"] == "seeded_successfully"
    assert res["predictions_count"] > 0
