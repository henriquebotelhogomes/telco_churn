"""M3 - Testes de telemetria (ring buffer) e drift (Evidently off critical path)."""

import time

import pandas as pd
import pytest

from churn_prediction.api import telemetry
from churn_prediction.config import settings
from churn_prediction.models import drift


@pytest.fixture(autouse=True)
def _estado_isolado():
    telemetry.drift_buffer.clear()
    drift.clear_cache()
    yield
    telemetry.drift_buffer.clear()
    drift.clear_cache()


def _dataset_com_variedade(base: dict, n: int = 20) -> list[dict]:
    contratos = ["Month-to-month", "One year", "Two year"]
    return [{**base, "Contract": contratos[i % 3], "tenure": i % 50} for i in range(n)]


def test_buffer_keeps_only_canonical_columns(canonical_customer_row):
    telemetry.drift_buffer.append({**canonical_customer_row, "customerID": "X-1"})
    df = telemetry.drift_buffer.to_dataframe()
    assert "customerID" not in df.columns
    assert "MonthlyCharges" in df.columns


def test_buffer_respects_maxlen(canonical_customer_row):
    pequeno = telemetry.DriftBuffer(maxlen=2)
    for i in range(5):
        pequeno.append({**canonical_customer_row, "tenure": i})
    assert len(pequeno) == 2
    assert [linha["tenure"] for linha in pequeno.buffer] == [3, 4]


def test_cache_estado_inicial():
    dados = drift.get_cached_report(0)
    assert dados["status"] == "not_computed"
    assert dados["report"] is None
    assert dados["age_seconds"] is None
    assert dados["cache_ttl_seconds"] == settings.drift_ttl_seconds


def test_refresh_dados_insuficientes(canonical_customer_row, monkeypatch):
    monkeypatch.setattr(settings, "drift_min_samples", 5)
    atual = pd.DataFrame([canonical_customer_row, canonical_customer_row])
    referencia = pd.DataFrame(_dataset_com_variedade(canonical_customer_row))
    resultado = drift.refresh_report(atual, reference_data=referencia)
    assert resultado["status"] == "ok"  # cache recém-atualizado
    assert resultado["report"]["status"] == "insufficient_data"
    assert resultado["report"]["samples"] == 2
    assert resultado["report"]["min_samples"] == 5


def test_refresh_referencia_indisponivel(canonical_customer_row, monkeypatch):
    monkeypatch.setattr(settings, "drift_min_samples", 1)
    monkeypatch.setattr(settings, "raw_data_path", settings.data_path / "nao_existe.csv")
    atual = pd.DataFrame([canonical_customer_row])
    resultado = drift.refresh_report(atual, reference_data=None)
    assert resultado["report"]["status"] == "reference_unavailable"


def test_refresh_roda_evidently_e_popula_cache(canonical_customer_row, monkeypatch):
    monkeypatch.setattr(settings, "drift_min_samples", 2)
    referencia = pd.DataFrame(_dataset_com_variedade(canonical_customer_row, n=30))
    # Current concentrado em "Two year" → drift categórico detectável
    atual = pd.DataFrame([{**canonical_customer_row, "Contract": "Two year"} for _ in range(15)])
    resultado = drift.refresh_report(atual, reference_data=referencia)
    report = resultado["report"]
    assert report["status"] == "ok"
    assert report["number_of_columns"] >= 10
    assert report["number_of_drifted_columns"] >= 1
    assert "drift_by_feature" in report
    assert report["drift_by_feature"]["Contract"]["drift_detected"] is True
    # Cache serve o mesmo relatório sem recalcular
    em_cache = drift.get_cached_report(len(atual))
    assert em_cache["status"] == "ok"
    assert em_cache["report"] is report
    assert em_cache["samples_in_buffer"] == 15


def test_cache_expira_por_ttl(canonical_customer_row, monkeypatch):
    monkeypatch.setattr(settings, "drift_min_samples", 1)
    monkeypatch.setattr(settings, "drift_ttl_seconds", 1)
    referencia = pd.DataFrame(_dataset_com_variedade(canonical_customer_row))
    atual = pd.DataFrame([canonical_customer_row])
    drift.refresh_report(atual, reference_data=referencia)
    drift._cache["generated_at"] = time.time() - 2
    assert drift.get_cached_report(1)["status"] == "stale"


def test_load_reference_data_usa_dataset_de_treino():
    referencia = drift.load_reference_data()
    assert referencia is not None
    assert "Churn" not in referencia.columns
    assert len(referencia) > 1000
