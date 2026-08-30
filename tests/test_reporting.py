import pytest
from fastapi.testclient import TestClient

from churn_prediction.api.main import app
from churn_prediction.db.session import init_db
from churn_prediction.models.reporting import executive_reporter


@pytest.mark.anyio
async def test_executive_report_data_and_html_generation():
    await init_db()

    data = await executive_reporter.get_report_data()
    assert "title" in data
    assert "financial_kpis" in data
    assert "total_customers_scored" in data["financial_kpis"]
    assert "playbooks_summary" in data
    assert "mlops_governance" in data
    assert "top_risk_accounts" in data

    html = executive_reporter.render_html_dossier(data)
    assert "<!DOCTYPE html>" in html
    assert "RetainIQ — Executive Retention Dossier" in html
    assert "MRR em Risco" in html
    assert "Governança e Saúde do Ecossistema MLOps" in html


def test_api_executive_report_endpoints():
    with TestClient(app) as client:
        # 1. Endpoint JSON
        resp_json = client.get("/api/v1/analytics/executive-report/data")
        assert resp_json.status_code == 200
        data = resp_json.json()
        assert "financial_kpis" in data
        assert "mlops_governance" in data

        # 2. Endpoint Download HTML
        resp_html = client.get("/api/v1/analytics/executive-report/download")
        assert resp_html.status_code == 200
        assert "text/html" in resp_html.headers["content-type"]
        assert "<!DOCTYPE html>" in resp_html.text
        assert "RetainIQ" in resp_html.text
