from fastapi.testclient import TestClient

from churn_prediction.api.main import app
from churn_prediction.models.copilot import RetentionCopilot


def test_copilot_deterministic_call_center():
    copilot = RetentionCopilot()
    res = copilot.generate_script(
        customer_id="7590-VHVEG",
        canal="call_center",
        tom="empatico",
        cliente={"tenure": 1, "MonthlyCharges": 29.85, "Contract": "Month-to-month"},
        fatores_shap=[
            {
                "fator": "Contrato: Mensal (Month-to-month)",
                "impacto_pct": 28.5,
                "direcao": "aumenta_churn",
            },
            {
                "fator": "Suporte Técnico: Ausente (No)",
                "impacto_pct": 19.2,
                "direcao": "aumenta_churn",
            },
        ],
        playbook="FIDELIZACAO_CONTRATO_ANUAL",
        reducao_estimada_risco=0.25,
        economia_esperada=120.0,
    )

    assert res["customer_id"] == "7590-VHVEG"
    assert res["canal"] == "call_center"
    assert res["tom"] == "empatico"
    assert (
        "abertura" in res["roteiro_etapas"]["etapa_1_abertura"].lower()
        or "olá" in res["roteiro_etapas"]["etapa_1_abertura"].lower()
    )
    assert "FIDELIZACAO_CONTRATO_ANUAL" in res["roteiro_etapas"]["etapa_3_proposta_valor"]
    assert len(res["argumentos_chave"]) >= 3
    assert res["provider_used"] == "deterministic_rules_engine"
    assert res["latency_ms"] >= 0.0


def test_copilot_tone_variations_differ():
    copilot = RetentionCopilot()
    cliente = {"tenure": 12, "MonthlyCharges": 80.0}
    fatores = [{"fator": "Contrato: Mensal", "direcao": "aumenta_churn"}]
    playbook = "FIDELIZACAO_CONTRATO_ANUAL"

    res_emp = copilot.generate_script(
        "CUST-1", "call_center", "empatico", cliente, fatores, playbook, 0.2, 100.0
    )
    res_dir = copilot.generate_script(
        "CUST-1", "call_center", "direto", cliente, fatores, playbook, 0.2, 100.0
    )
    res_con = copilot.generate_script(
        "CUST-1", "call_center", "consultivo", cliente, fatores, playbook, 0.2, 100.0
    )

    assert (
        res_emp["roteiro_etapas"]["etapa_1_abertura"]
        != res_dir["roteiro_etapas"]["etapa_1_abertura"]
    )
    assert (
        res_dir["roteiro_etapas"]["etapa_1_abertura"]
        != res_con["roteiro_etapas"]["etapa_1_abertura"]
    )
    assert "Cuidado ao Cliente" in res_emp["roteiro_etapas"]["etapa_1_abertura"]
    assert "Negociação RetainIQ" in res_dir["roteiro_etapas"]["etapa_1_abertura"]
    assert "Estratégicas RetainIQ" in res_con["roteiro_etapas"]["etapa_1_abertura"]


def test_copilot_deterministic_whatsapp():
    copilot = RetentionCopilot()
    res = copilot.generate_script(
        customer_id="1234-ABCD",
        canal="whatsapp",
        tom="direto",
        cliente={"tenure": 24, "MonthlyCharges": 89.90},
        fatores_shap=[
            {"fator": "Internet: Fibra Ótica", "impacto_pct": 15.0, "direcao": "aumenta_churn"}
        ],
        playbook="CROSS_SELL_PROTECAO_DIGITAL",
        reducao_estimada_risco=0.18,
        economia_esperada=85.0,
    )

    assert res["canal"] == "whatsapp"
    assert "CROSS_SELL_PROTECAO_DIGITAL" in res["mensagem_completa"]
    assert "1234-ABCD" in res["mensagem_completa"]
    assert "R$ 85.00" in res["mensagem_completa"]


def test_copilot_deterministic_email():
    copilot = RetentionCopilot()
    res = copilot.generate_script(
        customer_id="5555-XYZ",
        canal="email",
        tom="consultivo",
        cliente={"tenure": 36, "MonthlyCharges": 110.0},
        fatores_shap=[],
        playbook="DESCONTO_TEMPORARIO_15",
        reducao_estimada_risco=0.12,
        economia_esperada=198.0,
    )

    assert res["canal"] == "email"
    assert "Assunto:" in res["mensagem_completa"]
    assert "5555-XYZ" in res["mensagem_completa"]
    assert "DESCONTO_TEMPORARIO_15" in res["mensagem_completa"]


def test_api_generate_copilot_script_endpoint():
    with TestClient(app) as client:
        payload = {
            "customer_id": "7590-VHVEG",
            "canal": "whatsapp",
            "tom": "empatico",
            "cliente": {
                "tenure": 12,
                "MonthlyCharges": 70.0,
            },
            "fatores_shap": [
                {"fator": "Contrato: Mensal", "impacto_pct": 22.0, "direcao": "aumenta_churn"}
            ],
            "playbook": "FIDELIZACAO_CONTRATO_ANUAL",
            "reducao_estimada_risco": 0.20,
            "economia_esperada": 150.0,
        }

        resp = client.post("/api/v1/copilot/generate-script", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["customer_id"] == "7590-VHVEG"
        assert data["canal"] == "whatsapp"
        assert data["playbook_aplicado"] == "FIDELIZACAO_CONTRATO_ANUAL"
        assert "mensagem_completa" in data
        assert len(data["argumentos_chave"]) > 0
        assert data["provider_used"] in ["deterministic_rules_engine", "google_gemini", "openai"]


def test_copilot_gemini_mock(monkeypatch):
    import json

    copilot = RetentionCopilot()
    copilot.gemini_api_key = "fake-key"

    fake_response_json = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(
                                {
                                    "mensagem_completa": "Mensagem gerada via Gemini AI",
                                    "argumentos_chave": ["Ponto 1", "Ponto 2", "Ponto 3"],
                                    "resumo_estrategia": "Estratégia personalizada",
                                }
                            )
                        }
                    ]
                }
            }
        ]
    }

    class MockResponse:
        def read(self):
            return json.dumps(fake_response_json).encode("utf-8")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=6.0: MockResponse())

    res = copilot.generate_script(
        customer_id="GEMINI-123",
        canal="whatsapp",
        tom="empatico",
        cliente={"tenure": 10},
        fatores_shap=[],
        playbook="FIDELIZACAO",
    )

    assert res["provider_used"] == "google_gemini"
    assert res["mensagem_completa"] == "Mensagem gerada via Gemini AI"
    assert len(res["argumentos_chave"]) == 3
