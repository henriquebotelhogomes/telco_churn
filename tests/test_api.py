from fastapi.testclient import TestClient

# Importa a nossa aplicação FastAPI
from churn_prediction.api.main import app

# Instancia o cliente de testes
client = TestClient(app)


def test_health_check():
    """Testa se o endpoint de health check está respondendo corretamente."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    # Como o modelo é carregado no lifespan (que não roda por padrão no TestClient simples),
    # model_loaded pode ser false no teste isolado, o que é esperado neste contexto.
    assert "model_loaded" in data


def test_predict_churn_success():
    """Testa uma predição bem-sucedida com um payload válido."""

    # Payload válido em português (conforme nosso schema)
    payload = {
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

    # Usamos o TestClient com o gerenciador de contexto (with) para acionar o lifespan
    # Isso garante que o modelo seja carregado na memória antes do teste
    with TestClient(app) as live_client:
        response = live_client.post("/predict", json=payload)

        # Verifica se a requisição foi um sucesso
        assert response.status_code == 200

        data = response.json()

        # Verifica se a resposta contém as chaves esperadas
        assert "previsao_cancelamento" in data
        assert "probabilidade_cancelamento" in data

        # Verifica os tipos de dados retornados
        assert isinstance(data["previsao_cancelamento"], int)
        assert isinstance(data["probabilidade_cancelamento"], float)

        # A probabilidade deve estar entre 0 e 1
        assert 0.0 <= data["probabilidade_cancelamento"] <= 1.0


def test_predict_churn_validation_error():
    """Testa se a API rejeita payloads inválidos (ex: faltando campos obrigatórios)."""

    # Payload incompleto (faltam vários campos)
    payload_invalido = {"genero": "Feminino", "idoso": 0}

    with TestClient(app) as live_client:
        response = live_client.post("/predict", json=payload_invalido)

        # O Pydantic deve barrar a requisição e retornar 422 Unprocessable Entity
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
