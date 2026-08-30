"""M2 - Testes do contrato Pandera e da validação tolerante de lote."""

import pandas as pd
import pytest

from churn_prediction.data.contracts import (
    REQUIRED_COLUMNS,
    CustomerDataContract,
    MissingColumnsError,
    validate_customer_batch,
)


def test_required_columns_cover_model_features():
    for coluna in (
        "gender",
        "SeniorCitizen",
        "tenure",
        "Contract",
        "PaymentMethod",
        "MonthlyCharges",
        "TotalCharges",
    ):
        assert coluna in REQUIRED_COLUMNS


def test_contract_is_not_strict_and_coerces():
    config = CustomerDataContract.Config
    assert config.strict is False
    assert config.coerce is True


def test_valid_dataframe_passes(canonical_customer_row):
    df = pd.DataFrame([canonical_customer_row])
    validado = CustomerDataContract.validate(df)
    assert len(validado) == 1


def test_coerce_numeric_strings(canonical_customer_row):
    linha = {
        **canonical_customer_row,
        "tenure": "34",
        "MonthlyCharges": "70.5",
        "SeniorCitizen": "0",
    }
    resultado = validate_customer_batch(pd.DataFrame([linha]))
    assert len(resultado.valid) == 1
    assert resultado.invalid_rows == []
    assert resultado.valid["tenure"].iloc[0] == 34
    assert resultado.valid["MonthlyCharges"].iloc[0] == pytest.approx(70.5)


def test_invalid_rows_collected_without_failing_batch(canonical_customer_row):
    df = pd.DataFrame(
        [
            canonical_customer_row,
            {**canonical_customer_row, "Contract": "Lifetime"},
            {**canonical_customer_row, "MonthlyCharges": -10.0},
        ]
    )
    resultado = validate_customer_batch(df)
    assert len(resultado.valid) == 1
    assert resultado.valid.index.tolist() == [0]
    assert {linha["indice"] for linha in resultado.invalid_rows} == {1, 2}
    for linha in resultado.invalid_rows:
        assert linha["motivo"]


def test_original_positions_preserved_after_drop(canonical_customer_row):
    df = pd.DataFrame(
        [
            {**canonical_customer_row, "tenure": 999},
            canonical_customer_row,
            canonical_customer_row,
        ]
    )
    resultado = validate_customer_batch(df)
    assert resultado.valid.index.tolist() == [1, 2]
    assert [linha["indice"] for linha in resultado.invalid_rows] == [0]


def test_extra_columns_allowed(canonical_customer_row):
    df = pd.DataFrame([{**canonical_customer_row, "customerID": "7590-VHVEG", "Churn": "Yes"}])
    resultado = validate_customer_batch(df)
    assert len(resultado.valid) == 1
    assert "customerID" in resultado.valid.columns


def test_nullable_total_charges(canonical_customer_row):
    df = pd.DataFrame([{**canonical_customer_row, "TotalCharges": None}])
    resultado = validate_customer_batch(df)
    assert len(resultado.valid) == 1


def test_missing_column_raises(canonical_customer_row):
    df = pd.DataFrame([{k: v for k, v in canonical_customer_row.items() if k != "Contract"}])
    with pytest.raises(MissingColumnsError) as excinfo:
        validate_customer_batch(df)
    assert "Contract" in str(excinfo.value)
    assert excinfo.value.missing == ["Contract"]


def test_empty_dataframe_passes():
    df = pd.DataFrame(columns=REQUIRED_COLUMNS)
    resultado = validate_customer_batch(df)
    assert resultado.valid.empty
    assert resultado.invalid_rows == []
