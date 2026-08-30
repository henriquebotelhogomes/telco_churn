"""M2 - RetainIQ: contrato Pandera canônico EN-US e validação tolerante de lote."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import pandera as pa
from pandera.typing import Series

_YES_NO = ["Yes", "No"]
_YES_NO_NO_INTERNET = ["Yes", "No", "No internet service"]


class CustomerDataContract(pa.DataFrameModel):
    """Contrato canônico das features do modelo de churn (EN-US).

    strict=False: aceita colunas extras (customerID, Churn etc.).
    coerce=True: converte dtypes antes dos checks (CSV chega como object).
    """

    gender: Series[str] = pa.Field(isin=["Male", "Female"])
    SeniorCitizen: Series[int] = pa.Field(isin=[0, 1])
    Partner: Series[str] = pa.Field(isin=_YES_NO)
    Dependents: Series[str] = pa.Field(isin=_YES_NO)
    tenure: Series[int] = pa.Field(ge=0, le=120)
    PhoneService: Series[str] = pa.Field(isin=_YES_NO)
    MultipleLines: Series[str] = pa.Field(isin=["Yes", "No", "No phone service"])
    InternetService: Series[str] = pa.Field(isin=["DSL", "Fiber optic", "No"])
    OnlineSecurity: Series[str] = pa.Field(isin=_YES_NO_NO_INTERNET)
    OnlineBackup: Series[str] = pa.Field(isin=_YES_NO_NO_INTERNET)
    DeviceProtection: Series[str] = pa.Field(isin=_YES_NO_NO_INTERNET)
    TechSupport: Series[str] = pa.Field(isin=_YES_NO_NO_INTERNET)
    StreamingTV: Series[str] = pa.Field(isin=_YES_NO_NO_INTERNET)
    StreamingMovies: Series[str] = pa.Field(isin=_YES_NO_NO_INTERNET)
    Contract: Series[str] = pa.Field(isin=["Month-to-month", "One year", "Two year"])
    PaperlessBilling: Series[str] = pa.Field(isin=_YES_NO)
    PaymentMethod: Series[str] = pa.Field(
        isin=[
            "Electronic check",
            "Mailed check",
            "Bank transfer (automatic)",
            "Credit card (automatic)",
        ]
    )
    MonthlyCharges: Series[float] = pa.Field(ge=0.0)
    TotalCharges: Series[str] = pa.Field(nullable=True)

    class Config:
        strict = False
        coerce = True


REQUIRED_COLUMNS: list[str] = list(CustomerDataContract.to_schema().columns)


class MissingColumnsError(ValueError):
    """Lote sem as colunas canônicas obrigatórias."""

    def __init__(self, missing: list[str]) -> None:
        self.missing = missing
        super().__init__(f"Colunas obrigatórias ausentes: {', '.join(missing)}")


@dataclass
class BatchValidationResult:
    """Linhas válidas (índice preservado = posição no lote enviado) + inválidas."""

    valid: pd.DataFrame
    invalid_rows: list[dict[str, Any]] = field(default_factory=list)


def _extract_failures(
    error: pa.errors.SchemaError | pa.errors.SchemaErrors,
) -> tuple[dict[int, list[str]], list[str]]:
    """Separa falhas por linha ({indice: [motivos]}) e falhas de coluna (sem índice)."""
    row_failures: dict[int, list[str]] = {}
    column_failures: list[str] = []
    for _, case in error.failure_cases.iterrows():
        coluna = case.get("column")
        check = case.get("check")
        valor = case.get("failure_case")
        motivo = f"coluna '{coluna}' falhou em '{check}' (valor: {valor!r})"
        indice = case.get("index")
        if pd.isna(indice):
            column_failures.append(motivo)
        else:
            row_failures.setdefault(int(indice), []).append(motivo)
    return row_failures, column_failures


def validate_customer_batch(df: pd.DataFrame) -> BatchValidationResult:
    """Valida lote canônico EN-US sem derrubar o lote inteiro.

    O índice do DataFrame deve ser a posição da linha no lote enviado;
    ele é preservado em ``valid`` e usado em ``invalid_rows[*].indice``.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise MissingColumnsError(missing)

    invalid: dict[int, list[str]] = {}
    column_errors: list[str] = []
    data = df
    for _ in range(3):
        try:
            valid = CustomerDataContract.validate(data, lazy=True)
            break
        except (pa.errors.SchemaErrors, pa.errors.SchemaError) as err:
            row_failures, col_failures = _extract_failures(err)
            column_errors.extend(col_failures)
            if not row_failures:
                # Erro de coluna sem índice contamina todas as linhas restantes
                motivo = col_failures[-1] if col_failures else "linha inválida"
                for idx in data.index:
                    invalid.setdefault(int(idx), []).append(motivo)
                data = data.iloc[0:0]
                break
            for idx, motivos in row_failures.items():
                invalid.setdefault(idx, []).extend(motivos)
            data = data.drop(index=[i for i in row_failures if i in data.index])
            if data.empty:
                valid = data
                break
    else:
        for idx in data.index:
            invalid.setdefault(int(idx), []).append("linha inválida após revalidação")
        valid = data.iloc[0:0]

    invalid_rows = [
        {"indice": indice, "motivo": "; ".join(motivos)}
        for indice, motivos in sorted(invalid.items())
    ]
    if column_errors and not invalid_rows:
        invalid_rows = [{"indice": -1, "motivo": m} for m in column_errors]
    return BatchValidationResult(valid=valid, invalid_rows=invalid_rows)
