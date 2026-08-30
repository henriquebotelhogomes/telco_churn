"""M2 - RetainIQ: simulador What-If (4 ações canônicas, delta de risco e ROI)."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from typing import Any

import pandas as pd

ActionMutator = Callable[[dict[str, Any]], dict[str, Any]]

ACTION_MUTATORS: dict[str, ActionMutator] = {
    "fidelizacao": lambda row: {**row, "Contract": "Two year"},
    "protecao": lambda row: {**row, "TechSupport": "Yes", "OnlineSecurity": "Yes"},
    "autopagamento": lambda row: {**row, "PaymentMethod": "Credit card (automatic)"},
    "desconto_15": lambda row: {**row, "MonthlyCharges": float(row["MonthlyCharges"]) * 0.85},
}

# Ordem de tie-break por prioridade de negócio
ACTION_ORDER: list[str] = ["fidelizacao", "protecao", "autopagamento", "desconto_15"]

PLAYBOOKS: dict[str, tuple[str, str]] = {
    "fidelizacao": (
        "MIGRACAO_CONTRATO_ANUAL",
        "Oferecer 15% de desconto no plano anual com inclusao de Suporte Tecnico.",
    ),
    "protecao": ("CROSS_SELL_PROTECAO", "Ativar Suporte Tecnico e Seguranca Online."),
    "autopagamento": (
        "AUTOMATIZACAO_PAGAMENTO",
        "Migrar para pagamento automatico via cartao de credito.",
    ),
    "desconto_15": ("DESCONTO_RETENCAO", "Oferecer 15% de desconto na mensalidade."),
}

# Deltas iguais dentro desta tolerância seguem o tie-break de ACTION_ORDER
_TIE_TOLERANCE = 1e-9


def churn_probability(pipeline: Any, canonical_row: Mapping[str, Any]) -> float:
    """Probabilidade de churn via pipeline (nunca heurística)."""
    return float(pipeline.predict_proba(pd.DataFrame([dict(canonical_row)]))[0][1])


def simulate(
    pipeline: Any,
    canonical_row: Mapping[str, Any],
    action: str,
    original_probability: float | None = None,
) -> dict[str, float]:
    """Simula uma ação e recalcula o risco passando a linha mutada pelo pipeline."""
    if action not in ACTION_MUTATORS:
        raise ValueError(f"Ação desconhecida: '{action}'. Use uma de {ACTION_ORDER}")
    if original_probability is None:
        original_probability = churn_probability(pipeline, canonical_row)
    mutated = ACTION_MUTATORS[action](deepcopy(dict(canonical_row)))
    simulated_probability = churn_probability(pipeline, mutated)
    delta_risk = simulated_probability - original_probability  # negativo = reducao de risco
    roi = float(mutated["MonthlyCharges"]) * 12 * (-delta_risk) if delta_risk < 0 else 0.0
    return {
        "original_probability": original_probability,
        "simulated_probability": simulated_probability,
        "delta_risk": delta_risk,
        "roi_expected_annual_savings": round(roi, 2),
    }


def simulate_many(
    pipeline: Any,
    canonical_row: Mapping[str, Any],
    actions: Sequence[str] | None = None,
) -> dict[str, dict[str, float]]:
    """Simula várias ações reutilizando uma única predição original."""
    original_probability = churn_probability(pipeline, canonical_row)
    return {
        action: simulate(pipeline, canonical_row, action, original_probability)
        for action in (actions or ACTION_ORDER)
    }


def best_action(results: Mapping[str, Mapping[str, float]]) -> str | None:
    """Ação com maior redução de risco; tie-break por ACTION_ORDER.

    Retorna None se nenhuma ação reduzir o risco.
    """
    best_key: str | None = None
    best_delta = 0.0
    for key in ACTION_ORDER:
        if key not in results:
            continue
        delta = float(results[key]["delta_risk"])
        if best_key is None or delta < best_delta - _TIE_TOLERANCE:
            best_key, best_delta = key, delta
    if best_key is None or best_delta >= -_TIE_TOLERANCE:
        return None
    return best_key
