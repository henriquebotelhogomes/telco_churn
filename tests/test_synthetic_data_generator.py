import pytest
from starlette.testclient import TestClient

from churn_prediction.api.main import app
from churn_prediction.data.contracts import CustomerDataContract
from churn_prediction.data.generate_enterprise_dataset import generate_enterprise_dataset


@pytest.fixture
def client():
    return TestClient(app)


def test_generate_enterprise_dataset_structure_and_contracts():
    """Testa se o gerador produz um dataset válido conforme o contrato Pandera e com colunas extras."""
    df = generate_enterprise_dataset(num_samples=250, chaos_ratio=0.15, seed=123)

    assert len(df) == 250
    assert len(df.columns) >= 35

    # Valida contrato Pandera
    validated = CustomerDataContract.validate(df)
    assert len(validated) == 250

    # Valida presença das novas colunas corporativas
    assert "operator" in df.columns
    assert "region_uf" in df.columns
    assert "avg_latency_ms" in df.columns
    assert "fiber_outages_count_90d" in df.columns
    assert "nps_score" in df.columns
    assert "whatsapp_sentiment_score" in df.columns

    # Verifica distribuição multi-tenant
    ops = set(df["operator"].unique())
    assert "Vivo" in ops
    assert "Claro" in ops
    assert "TIM" in ops


def test_synthesize_dataset_rest_endpoint(client: TestClient):
    """Testa o endpoint REST de geração de base sintética sob demanda."""
    response = client.post(
        "/api/v1/admin/data/synthesize-enterprise-dataset",
        json={"num_samples": 300, "chaos_ratio": 0.10, "save_as_default": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_records"] == 300
    assert data["total_columns"] >= 35
    assert "operators_distribution" in data
    assert "Vivo" in data["operators_distribution"]
    assert len(data["csv_sample_preview"]) == 5
