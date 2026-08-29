import joblib
import pytest

from churn_prediction.config import settings


@pytest.fixture(scope="session")
def churn_pipeline():
    """Carrega pipeline treinado para testes de SHAP."""
    return joblib.load(settings.model_path)
