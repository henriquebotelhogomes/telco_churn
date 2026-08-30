import joblib
import pytest

from churn_prediction.config import settings


@pytest.fixture(scope="session")
def churn_pipeline():
    """Carrega pipeline treinado para testes de SHAP."""
    return joblib.load(settings.model_path)


@pytest.fixture()
def canonical_customer_row():
    """Linha canônica EN-US de alto risco (espelho do VALID_PAYLOAD PT-BR)."""
    return {
        "gender": "Female",
        "SeniorCitizen": 0,
        "Partner": "Yes",
        "Dependents": "No",
        "tenure": 1,
        "PhoneService": "No",
        "MultipleLines": "No phone service",
        "InternetService": "DSL",
        "OnlineSecurity": "No",
        "OnlineBackup": "Yes",
        "DeviceProtection": "No",
        "TechSupport": "No",
        "StreamingTV": "No",
        "StreamingMovies": "No",
        "Contract": "Month-to-month",
        "PaperlessBilling": "Yes",
        "PaymentMethod": "Electronic check",
        "MonthlyCharges": 29.85,
        "TotalCharges": "29.85",
    }
