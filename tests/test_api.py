import pandas as pd
import pytest
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

# Perfil de baixo risco para exercitar a distribuição do resumo batch
VALID_PAYLOAD_2 = {
    **VALID_PAYLOAD,
    "meses_permanencia": 42,
    "contrato": "Dois anos",
    "metodo_pagamento": "Cartão de crédito",
    "cobranca_total": "1253.7",
}


def _csv_bytes(rows: list[dict]) -> bytes:
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


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


# ---------------------------------------------------------------------------
# M2 — POST /api/v1/predict/batch
# ---------------------------------------------------------------------------


def test_predict_batch_json_valid():
    """Lote JSON PT-BR válido retorna results + resumo consistente."""
    with TestClient(app) as live_client:
        response = live_client.post("/api/v1/predict/batch", json=[VALID_PAYLOAD, VALID_PAYLOAD_2])
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert data["linhas_invalidas"] == []

        resumo = data["resumo"]
        assert resumo["total_analisado"] == 2
        dist = resumo["distribuicao_risco"]
        assert dist["baixo"] + dist["medio"] + dist["alto"] + dist["critico"] == 2
        assert resumo["total_em_risco"] == dist["alto"] + dist["critico"]

        for linha in data["results"]:
            assert linha["nivel_risco"] in ("Baixo", "Médio", "Alto", "Crítico")
            assert 0.0 <= linha["probabilidade_cancelamento"] <= 1.0
            if linha["nivel_risco"] in ("Alto", "Crítico"):
                assert linha["mrr_em_risco"] > 0
            else:
                assert linha["mrr_em_risco"] == 0.0

        assert resumo["mrr_total_em_risco"] == pytest.approx(
            sum(linha["mrr_em_risco"] for linha in data["results"]), abs=0.05
        )


def test_predict_batch_json_invalid_row_does_not_fail_batch():
    """Item inválido vira linhas_invalidas sem derrubar o restante do lote."""
    with TestClient(app) as live_client:
        response = live_client.post(
            "/api/v1/predict/batch", json=[VALID_PAYLOAD, {"genero": "Outro"}]
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert len(data["linhas_invalidas"]) == 1
        invalida = data["linhas_invalidas"][0]
        assert invalida["indice"] == 1
        assert "genero" in invalida["motivo"]
        assert data["resumo"]["total_analisado"] == 1


def test_predict_batch_json_not_array():
    with TestClient(app) as live_client:
        response = live_client.post("/api/v1/predict/batch", json={"cliente": VALID_PAYLOAD})
        assert response.status_code == 422


def test_predict_batch_no_body():
    with TestClient(app) as live_client:
        response = live_client.post("/api/v1/predict/batch")
        assert response.status_code == 422


def test_predict_batch_csv_valid(canonical_customer_row):
    """CSV EN-US cru (com customerID e coluna Churn ignorada) é aceito."""
    rows = [
        {**canonical_customer_row, "customerID": "A-1", "Churn": "Yes"},
        {
            **canonical_customer_row,
            "customerID": "A-2",
            "Contract": "Two year",
            "tenure": 40,
            "Churn": "No",
        },
    ]
    with TestClient(app) as live_client:
        response = live_client.post(
            "/api/v1/predict/batch",
            files={"file": ("clientes.csv", _csv_bytes(rows), "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert data["linhas_invalidas"] == []
        assert {linha["customer_id"] for linha in data["results"]} == {"A-1", "A-2"}
        assert data["resumo"]["total_analisado"] == 2


def test_predict_batch_csv_invalid_rows(canonical_customer_row):
    """Linha com valor fora do contrato é reportada sem derrubar o lote."""
    rows = [
        canonical_customer_row,
        {**canonical_customer_row, "Contract": "Vitalício"},
    ]
    with TestClient(app) as live_client:
        response = live_client.post(
            "/api/v1/predict/batch",
            files={"file": ("clientes.csv", _csv_bytes(rows), "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["linhas_invalidas"][0]["indice"] == 1
        assert "Contract" in data["linhas_invalidas"][0]["motivo"]


def test_predict_batch_csv_missing_columns():
    with TestClient(app) as live_client:
        response = live_client.post(
            "/api/v1/predict/batch",
            files={"file": ("errado.csv", b"foo,bar\n1,2\n", "text/csv")},
        )
        assert response.status_code == 422
        assert "obrigat" in response.json()["detail"]


def test_predict_batch_csv_empty_file():
    with TestClient(app) as live_client:
        response = live_client.post(
            "/api/v1/predict/batch",
            files={"file": ("vazio.csv", b"   ", "text/csv")},
        )
        assert response.status_code == 422


def test_predict_batch_csv_no_file_field():
    with TestClient(app) as live_client:
        response = live_client.post(
            "/api/v1/predict/batch",
            data={"outro_campo": "valor"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# M2 — POST /api/v1/simulate
# ---------------------------------------------------------------------------


def test_simulate_default_all_actions():
    """Sem informar ações, simula as 4 canônicas em ordem determinística."""
    with TestClient(app) as live_client:
        response = live_client.post("/api/v1/simulate", json={"cliente": VALID_PAYLOAD})
        assert response.status_code == 200
        data = response.json()
        assert 0.0 <= data["original_probability"] <= 1.0
        acoes = [r["acao"] for r in data["resultados"]]
        assert acoes == ["fidelizacao", "protecao", "autopagamento", "desconto_15"]
        for resultado in data["resultados"]:
            assert resultado["playbook"]
            assert resultado["descricao"]
            assert resultado["delta_risk"] == pytest.approx(
                resultado["simulated_probability"] - resultado["original_probability"]
            )
            assert resultado["roi_expected_annual_savings"] >= 0.0
        if data["melhor_acao"] is not None:
            assert data["melhor_acao"] in acoes


def test_simulate_subset_with_roi_consistency():
    """Simula apenas desconto_15 e valida a fórmula de ROI."""
    with TestClient(app) as live_client:
        response = live_client.post(
            "/api/v1/simulate",
            json={"cliente": VALID_PAYLOAD, "acoes": ["desconto_15"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["resultados"]) == 1
        resultado = data["resultados"][0]
        assert resultado["acao"] == "desconto_15"
        if resultado["delta_risk"] < 0:
            roi_esperado = round(
                VALID_PAYLOAD["cobranca_mensal"] * 0.85 * 12 * -resultado["delta_risk"], 2
            )
            assert resultado["roi_expected_annual_savings"] == pytest.approx(roi_esperado)
        else:
            assert resultado["roi_expected_annual_savings"] == 0.0


def test_simulate_invalid_action():
    with TestClient(app) as live_client:
        response = live_client.post(
            "/api/v1/simulate",
            json={"cliente": VALID_PAYLOAD, "acoes": ["voo_gratis"]},
        )
        assert response.status_code == 422
