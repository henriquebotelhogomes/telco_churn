"""M2 - Testes do simulador What-If (4 ações canônicas, delta e ROI)."""

import pytest

from churn_prediction.models import simulator


def test_action_order_matches_mutators_and_playbooks():
    assert simulator.ACTION_ORDER == list(simulator.ACTION_MUTATORS)
    assert set(simulator.PLAYBOOKS) == set(simulator.ACTION_ORDER)


def test_mutators_apply_canonical_changes(canonical_customer_row):
    fidelizacao = simulator.ACTION_MUTATORS["fidelizacao"](canonical_customer_row)
    assert fidelizacao["Contract"] == "Two year"

    protecao = simulator.ACTION_MUTATORS["protecao"](canonical_customer_row)
    assert protecao["TechSupport"] == "Yes"
    assert protecao["OnlineSecurity"] == "Yes"

    autopagamento = simulator.ACTION_MUTATORS["autopagamento"](canonical_customer_row)
    assert autopagamento["PaymentMethod"] == "Credit card (automatic)"

    desconto = simulator.ACTION_MUTATORS["desconto_15"](canonical_customer_row)
    assert desconto["MonthlyCharges"] == pytest.approx(
        canonical_customer_row["MonthlyCharges"] * 0.85
    )

    # A linha original nunca é mutada
    assert canonical_customer_row["Contract"] == "Month-to-month"
    assert canonical_customer_row["TechSupport"] == "No"


def test_simulate_returns_contract_shape(churn_pipeline, canonical_customer_row):
    resultado = simulator.simulate(churn_pipeline, canonical_customer_row, "fidelizacao")
    assert set(resultado) == {
        "original_probability",
        "simulated_probability",
        "delta_risk",
        "roi_expected_annual_savings",
    }
    assert 0.0 <= resultado["original_probability"] <= 1.0
    assert 0.0 <= resultado["simulated_probability"] <= 1.0
    assert resultado["delta_risk"] == pytest.approx(
        resultado["simulated_probability"] - resultado["original_probability"]
    )
    # Perfil de alto risco (mensal + cheque eletrônico + 1 mês): fidelização reduz risco
    assert resultado["delta_risk"] < 0
    roi_esperado = round(
        canonical_customer_row["MonthlyCharges"] * 12 * -resultado["delta_risk"], 2
    )
    assert resultado["roi_expected_annual_savings"] == pytest.approx(roi_esperado)


def test_simulate_reuses_provided_original_probability(churn_pipeline, canonical_customer_row):
    resultado = simulator.simulate(
        churn_pipeline, canonical_customer_row, "protecao", original_probability=0.42
    )
    assert resultado["original_probability"] == 0.42
    assert resultado["delta_risk"] == pytest.approx(resultado["simulated_probability"] - 0.42)


def test_simulate_unknown_action_raises(churn_pipeline, canonical_customer_row):
    with pytest.raises(ValueError, match="voo_gratis"):
        simulator.simulate(churn_pipeline, canonical_customer_row, "voo_gratis")


def test_simulate_many_returns_all_actions_in_order(churn_pipeline, canonical_customer_row):
    resultados = simulator.simulate_many(churn_pipeline, canonical_customer_row)
    assert list(resultados) == simulator.ACTION_ORDER
    # Probabilidade original calculada uma única vez e reutilizada
    originais = {r["original_probability"] for r in resultados.values()}
    assert len(originais) == 1


def test_simulate_many_subset(churn_pipeline, canonical_customer_row):
    resultados = simulator.simulate_many(churn_pipeline, canonical_customer_row, ["desconto_15"])
    assert list(resultados) == ["desconto_15"]


def test_best_action_returns_lowest_delta(churn_pipeline, canonical_customer_row):
    resultados = simulator.simulate_many(churn_pipeline, canonical_customer_row)
    melhor = simulator.best_action(resultados)
    assert melhor is not None
    deltas = {acao: r["delta_risk"] for acao, r in resultados.items()}
    assert deltas[melhor] == pytest.approx(min(deltas.values()))


def test_best_action_tie_break_and_no_reduction():
    empate = {acao: {"delta_risk": -0.1} for acao in simulator.ACTION_ORDER}
    assert simulator.best_action(empate) == "fidelizacao"

    sem_reducao = {acao: {"delta_risk": 0.02} for acao in simulator.ACTION_ORDER}
    assert simulator.best_action(sem_reducao) is None

    assert simulator.best_action({}) is None
