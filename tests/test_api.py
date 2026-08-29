from fastapi.testclient import TestClient

from churn_prediction.api.main import app

client = TestClient(app)

VALID_PAYLOAD = {
    "genero": "Feminino",
    "idoso": 0,
    "tem_parceiro": "Sim",
    "tem_dependentes": "Não",
    "meses_permanencia": 1,
    "servico_telefone": "Não",
    "multiplas_linhas": "Sem serviço de telefone",
    "servico_internet": "DSL",
    "seguranca_online": "Não",
    "backup_online": "Sim",
    "protecao_dispositivo": "Não",
    "suporte_tecnico": "Não",
    "streaming_tv": "Não",
    "streaming_filmes": "Não",
    "contrato": "Mensal",
    "faturamento_sem_papel": "Sim",
    "metodo_pagamento": "Cheque eletrônico",
    "cobranca_mensal": 29.85,
    "cobranca_total": "29.85",
}


def test_health_check():
    """Testa se o endpoint de health check está respondendo corretamente."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data


def test_predict_churn_success_v1():
    """Testa POST /api/v1/predict com payload válido (RetainIQ M1)."""
    with TestClient(app) as live_client:
        response = live_client.post("/api/v1/predict", json=VALID_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        # Campos basicos
        assert "previsao_cancelamento" in data
        assert "probabilidade_cancelamento" in data
        assert isinstance(data["previsao_cancelamento"], int)
        assert isinstance(data["probabilidade_cancelamento"], float)
        assert 0.0 <= data["probabilidade_cancelamento"] <= 1.0
        # M1 - novos campos
        assert "nivel_risco" in data
        assert data["nivel_risco"] in ("Baixo", "Médio", "Alto", "Crítico")
        assert "mrr_em_risco" in data
        assert isinstance(data["mrr_em_risco"], float)
        assert "top_fatores_risco" in data
        assert isinstance(data["top_fatores_risco"], list)
        assert 1 <= len(data["top_fatores_risco"]) <= 3
        for fator in data["top_fatores_risco"]:
            assert "fator" in fator
            assert "impacto" in fator
            assert "%" in fator["impacto"]
            assert "shap_value" in fator
            assert "direcao" in fator
            assert fator["direcao"] in ("aumenta_risco", "reduz_risco")
            assert "descricao" in fator
        # acao_recomendada pode ser None se nenhuma acao reduz risco
        assert "acao_recomendada" in data
        if data["acao_recomendada"] is not None:
            assert "playbook" in data["acao_recomendada"]
            assert "descricao" in data["acao_recomendada"]
            assert "reducao_estimada_risco" in data["acao_recomendada"]
        # P95 < 50ms nao testado aqui (requer benchmark), mas endpoint deve responder rapido
        # Verifica se mrr coerente com nivel
        if data["nivel_risco"] in ("Alto", "Crítico"):
            assert data["mrr_em_risco"] > 0
        else:
            # Baixo/Medio -> mrr 0 (definicao M1)
            assert data["mrr_em_risco"] == 0.0


def test_legacy_predict_removed():
    """Rota legada /predict deve retornar 404 (breaking change M0/M1)."""
    with TestClient(app) as live_client:
        response = live_client.post("/predict", json=VALID_PAYLOAD)
        assert response.status_code == 404


def test_predict_churn_validation_error():
    """Testa se a API rejeita payloads inválidos."""
    payload_invalido = {"genero": "Feminino", "idoso": 0}
    with TestClient(app) as live_client:
        response = live_client.post("/api/v1/predict", json=payload_invalido)
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
