from fastapi.testclient import TestClient

from churn_prediction.api.main import app


def test_list_models_registry():
    """Testa o endpoint de listagem do Model Registry (M7)."""
    with TestClient(app) as client:
        res = client.get("/api/v1/models")
        assert res.status_code == 200
        data = res.json()
        assert "active_champion" in data
        assert "models" in data
        assert len(data["models"]) >= 1

        # Verifica se as métricas essenciais estão presentes
        first = data["models"][0]
        assert "model_name" in first
        assert "metrics" in first
        assert "roc_auc" in first["metrics"]


def test_promote_model_endpoint():
    """Testa promoção dinâmica de modelo via API (M7)."""
    with TestClient(app) as client:
        # Tenta promover um modelo existente
        payload = {"model_name": "churn-random-forest"}
        res = client.post("/api/v1/models/promote", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["new_champion"] == "churn-random-forest"
        assert data["status"] == "promoted_successfully"

        # Verifica se o endpoint de listagem reflete a promoção
        list_res = client.get("/api/v1/models")
        assert list_res.json()["active_champion"] == "churn-random-forest"

        # Retorna para o XGBoost para manter o padrão
        res_back = client.post("/api/v1/models/promote", json={"model_name": "churn-xgboost"})
        assert res_back.status_code == 200

        # Tenta promover modelo inexistente
        err_res = client.post("/api/v1/models/promote", json={"model_name": "modelo-inexistente"})
        assert err_res.status_code == 404


def test_shadow_metrics_endpoint():
    """Testa endpoint de telemetria de shadow scoring (M7)."""
    with TestClient(app) as client:
        # Faz uma predição individual para gerar shadow score
        payload = {
            "genero": "Feminino",
            "idoso": 0,
            "tem_parceiro": "Sim",
            "tem_dependentes": "Não",
            "meses_permanencia": 6,
            "servico_telefone": "Sim",
            "multiplas_linhas": "Não",
            "servico_internet": "Fibra ótica",
            "seguranca_online": "Não",
            "backup_online": "Não",
            "protecao_dispositivo": "Não",
            "suporte_tecnico": "Não",
            "streaming_tv": "Sim",
            "streaming_filmes": "Sim",
            "contrato": "Mensal",
            "faturamento_sem_papel": "Sim",
            "metodo_pagamento": "Cheque eletrônico",
            "cobranca_mensal": 89.90,
            "cobranca_total": "539.40",
        }
        pred_res = client.post("/api/v1/predict", json=payload)
        assert pred_res.status_code == 200

        # Consulta métricas de shadow
        res = client.get("/api/v1/models/shadow-metrics")
        assert res.status_code == 200
        data = res.json()
        assert "total_shadow_scored" in data
        assert "avg_concordance_pct" in data
        assert "model_comparisons" in data
