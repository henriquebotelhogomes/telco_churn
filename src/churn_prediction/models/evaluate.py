import pandas as pd
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.pipeline import Pipeline


def evaluate_model(model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict[str, float]:
    """
    Avalia o modelo e retorna as principais métricas.
    """
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    roc_auc = roc_auc_score(y_test, y_prob)

    print("\n" + "=" * 50)
    print("📊 RELATÓRIO DE CLASSIFICAÇÃO")
    print("=" * 50)
    print(classification_report(y_test, y_pred))
    print(f"ROC-AUC Score: {roc_auc:.4f}")
    print("=" * 50 + "\n")

    return {"roc_auc": float(roc_auc)}
