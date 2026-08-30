import pandas as pd

from churn_prediction.models.explainability import ChurnExplainer, nivel_risco


def test_nivel_risco_thresholds():
    """Thresholds centralizados em config.py, nao hard-coded."""
    assert nivel_risco(0.10) == "Baixo"
    assert nivel_risco(0.29) == "Baixo"
    assert nivel_risco(0.30) == "Médio"
    assert nivel_risco(0.59) == "Médio"
    assert nivel_risco(0.60) == "Alto"
    assert nivel_risco(0.79) == "Alto"
    assert nivel_risco(0.80) == "Crítico"
    assert nivel_risco(0.99) == "Crítico"


def test_explainer_top3_structure(churn_pipeline):
    """ChurnExplainer retorna Top 3 com impacto % + shap_value bruto."""
    # churn_pipeline fixture vem de conftest (carrega joblib)
    explainer = ChurnExplainer(churn_pipeline)
    # Payload canonico EN-US
    raw = pd.DataFrame(
        [
            {
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
        ]
    )
    result = explainer.explain_instance(raw)
    assert isinstance(result, list)
    assert 1 <= len(result) <= 3
    for item in result:
        assert "fator" in item
        assert "impacto" in item
        assert "%" in item["impacto"]
        # impacto deve ser string tipo +28% ou -12%
        assert item["impacto"][0] in ("+", "-")
        assert "shap_value" in item
        assert isinstance(item["shap_value"], float)
        assert "direcao" in item
        assert item["direcao"] in ("aumenta_risco", "reduz_risco")
        assert "descricao" in item
        # consistencia direcao vs sinal shap
        if item["shap_value"] > 0:
            assert item["direcao"] == "aumenta_risco"
        elif item["shap_value"] < 0:
            assert item["direcao"] == "reduz_risco"
        # Impacto magnitude ordenado? Verifica que lista esta ordenada por |impacto|
    # Verifica ordenacao por magnitude
    magnitudes = [abs(float(x["impacto"].strip("%+"))) for x in result]
    assert magnitudes == sorted(magnitudes, reverse=True)


def test_explainer_uses_preprocessor_not_adhoc(churn_pipeline):
    """Garante que explainer usa preprocessor do pipeline, nao transformacao solta."""
    explainer = ChurnExplainer(churn_pipeline)
    # feature_names deve vir do ColumnTransformer
    assert len(explainer.feature_names) > 10
    # Nenhum nome deve conter prefixo tecnico cru com __ se limpo corretamente
    for name in explainer.feature_names:
        assert "__" not in name
