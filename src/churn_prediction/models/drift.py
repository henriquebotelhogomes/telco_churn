"""M3 - RetainIQ: data drift via Evidently, sempre fora do caminho crítico.

A inferência nunca roda o Evidently: apenas alimenta o ring buffer
(``churn_prediction.api.telemetry``). ``GET /api/v1/metrics/drift`` lê o
cache com TTL e ``POST /api/v1/admin/drift/refresh`` é o único ponto que
dispara o cálculo.
"""

from __future__ import annotations

import time
from typing import Any

import pandas as pd

from churn_prediction.config import settings
from churn_prediction.data.contracts import REQUIRED_COLUMNS

# Cache consumido por GET /api/v1/metrics/drift (nunca calcula)
_cache: dict[str, Any] = {"report": None, "generated_at": None}


def load_reference_data() -> pd.DataFrame | None:
    """Baseline de drift: dataset de treino (MVP). None se o arquivo não existir."""
    if not settings.raw_data_path.exists():
        return None
    reference = pd.read_csv(settings.raw_data_path)
    if "Churn" in reference.columns:
        reference = reference.drop(columns=["Churn"])
    return reference


def generate_drift_report(
    reference_data: pd.DataFrame, current_data: pd.DataFrame
) -> dict[str, Any]:
    """Roda o DataDriftPreset do Evidently e devolve um resumo compacto."""
    from evidently.legacy.metric_preset import DataDriftPreset
    from evidently.legacy.report import Report

    columns = [
        coluna
        for coluna in REQUIRED_COLUMNS
        if coluna in reference_data.columns and coluna in current_data.columns
    ]
    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference_data[columns], current_data=current_data[columns])

    summary: dict[str, Any] = {"status": "ok"}
    drift_by_feature: dict[str, Any] = {}
    for metric in report.as_dict().get("metrics", []):
        result = metric.get("result", {})
        for key in (
            "number_of_columns",
            "number_of_drifted_columns",
            "share_of_drifted_columns",
            "dataset_drift",
        ):
            if key in result:
                summary[key] = result[key]
        for coluna, detalhes in (result.get("drift_by_columns") or {}).items():
            drift_by_feature[coluna] = {
                "column_type": detalhes.get("column_type"),
                "stattest_name": detalhes.get("stattest_name"),
                "drift_score": detalhes.get("drift_score"),
                "drift_detected": bool(detalhes.get("drift_detected")),
            }
    if drift_by_feature:
        summary["drift_by_feature"] = drift_by_feature
    return summary


def get_cached_report(samples_in_buffer: int) -> dict[str, Any]:
    """Lê o cache aplicando o TTL. Nunca dispara cálculo (caminho crítico)."""
    report = _cache["report"]
    generated_at = _cache["generated_at"]
    now = time.time()
    if report is None:
        status = "not_computed"
    elif generated_at is None or now - generated_at > settings.drift_ttl_seconds:
        status = "stale"
    else:
        status = "ok"
    return {
        "status": status,
        "generated_at": generated_at,
        "age_seconds": None if generated_at is None else round(now - generated_at, 1),
        "cache_ttl_seconds": settings.drift_ttl_seconds,
        "samples_in_buffer": samples_in_buffer,
        "report": report,
    }


def refresh_report(
    current_data: pd.DataFrame, reference_data: pd.DataFrame | None = None
) -> dict[str, Any]:
    """Recalcula o drift e atualiza o cache.

    Chamado exclusivamente por POST /api/v1/admin/drift/refresh.
    """
    samples = int(len(current_data))
    if samples < settings.drift_min_samples:
        report: dict[str, Any] = {
            "status": "insufficient_data",
            "samples": samples,
            "min_samples": settings.drift_min_samples,
        }
    else:
        reference = reference_data if reference_data is not None else load_reference_data()
        if reference is None:
            report = {"status": "reference_unavailable"}
        else:
            report = generate_drift_report(reference, current_data)
    _cache["report"] = report
    _cache["generated_at"] = time.time()
    return get_cached_report(samples)


def clear_cache() -> None:
    """Limpa o cache (usado em testes)."""
    _cache["report"] = None
    _cache["generated_at"] = None
