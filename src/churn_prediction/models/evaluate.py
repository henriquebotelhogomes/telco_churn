import time
from typing import Any

import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline


def evaluate_model(model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict[str, Any]:
    """
    Avalia o modelo de classificação e retorna conjunto completo de métricas de ML e latência.
    """
    t0 = time.perf_counter()
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    elapsed_ms = (time.perf_counter() - t0) * 1000
    latency_per_sample_ms = elapsed_ms / len(X_test) if len(X_test) > 0 else 0.0

    roc_auc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)
    recall = recall_score(y_test, y_pred, zero_division=0)
    precision = precision_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    brier = brier_score_loss(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred).tolist()

    print("\n" + "=" * 50)
    print("[EVAL] RELATORIO DE CLASSIFICACAO")
    print("=" * 50)
    print(classification_report(y_test, y_pred, zero_division=0))
    print(f"ROC-AUC: {roc_auc:.4f} | PR-AUC: {pr_auc:.4f} | Brier: {brier:.4f}")
    print(f"Latência média por inferência: {latency_per_sample_ms:.3f} ms")
    print("=" * 50 + "\n")

    return {
        "roc_auc": round(float(roc_auc), 4),
        "pr_auc": round(float(pr_auc), 4),
        "f1": round(float(f1), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "brier_score": round(float(brier), 4),
        "latency_ms": round(float(latency_per_sample_ms), 3),
        "confusion_matrix": cm,
    }
