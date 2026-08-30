import json
import subprocess
from datetime import UTC, datetime
from typing import Any

import joblib
import sklearn
import xgboost
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from churn_prediction.config import settings
from churn_prediction.data.preprocess import get_preprocessing_pipeline, load_and_split_data
from churn_prediction.models.evaluate import evaluate_model


def _git_sha() -> str | None:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except Exception:
        return None


def train() -> dict[str, Any]:
    """
    Pipeline completo de treinamento Multi-Model: treina Champion (XGBoost)
    e Challengers (Random Forest, HistGradientBoosting, Logistic Regression).
    Gera artefatos individuais e o catálogo central models/registry.json.
    """
    print("[TRAIN] Iniciando pipeline de treinamento multi-modelo...")

    # 1. Carregar os dados
    print(f"[DATA] Carregando dados de: {settings.raw_data_path}")
    X, y = load_and_split_data(settings.raw_data_path)

    # 2. Divisão Treino/Teste estratificada
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=settings.test_size, random_state=settings.random_state, stratify=y
    )
    print(f"[DATA] Dados divididos: {len(X_train)} treino | {len(X_test)} teste")

    pos_weight = (len(y_train) - y_train.sum()) / y_train.sum()
    git_sha = _git_sha()
    settings.model_dir.mkdir(parents=True, exist_ok=True)

    # Definição dos algoritmos candidatos
    model_candidates = [
        {
            "name": "churn-xgboost",
            "algo": "XGBoost",
            "role": "champion",
            "version": "1.0.0",
            "filename": "churn_model_pipeline.joblib",
            "classifier": XGBClassifier(
                random_state=settings.random_state,
                scale_pos_weight=pos_weight,
                eval_metric="logloss",
            ),
        },
        {
            "name": "churn-random-forest",
            "algo": "Random Forest",
            "role": "challenger",
            "version": "1.0.0",
            "filename": "churn_random_forest.joblib",
            "classifier": RandomForestClassifier(
                n_estimators=100,
                class_weight="balanced",
                random_state=settings.random_state,
            ),
        },
        {
            "name": "churn-gradient-boosting",
            "algo": "HistGradientBoosting",
            "role": "challenger",
            "version": "1.0.0",
            "filename": "churn_gradient_boosting.joblib",
            "classifier": HistGradientBoostingClassifier(
                class_weight="balanced",
                random_state=settings.random_state,
            ),
        },
        {
            "name": "churn-logistic-regression",
            "algo": "Logistic Regression",
            "role": "baseline",
            "version": "1.0.0",
            "filename": "churn_logistic_regression.joblib",
            "classifier": LogisticRegression(
                class_weight="balanced",
                max_iter=1000,
                random_state=settings.random_state,
            ),
        },
    ]

    registry_entries: list[dict[str, Any]] = []

    for candidate in model_candidates:
        name = candidate["name"]
        print(f"\n[MODEL] Treinando modelo candidato: {name} ({candidate['algo']})...")
        pipeline = Pipeline(
            steps=[
                ("preprocessing", get_preprocessing_pipeline()),
                ("classifier", candidate["classifier"]),
            ]
        )
        pipeline.fit(X_train, y_train)

        metrics = evaluate_model(pipeline, X_test, y_test)
        artifact_path = settings.model_dir / candidate["filename"]
        joblib.dump(pipeline, artifact_path)
        print(f"[OK] Artefato salvo em: {artifact_path}")

        meta = {
            "model_name": name,
            "version": candidate["version"],
            "algo": candidate["algo"],
            "role": candidate["role"],
            "trained_at": datetime.now(UTC).isoformat(),
            "framework_versions": {
                "xgboost": xgboost.__version__,
                "scikit-learn": sklearn.__version__,
            },
            "dataset": {
                "path": str(settings.raw_data_path),
                "rows": int(len(X)),
                "columns": [str(col) for col in X.columns],
                "positive_rate": round(float(y.mean()), 4),
            },
            "split": {
                "test_size": settings.test_size,
                "random_state": settings.random_state,
            },
            "metrics": metrics,
            "risk_thresholds": settings.risk_thresholds,
            "artifact": str(artifact_path),
            "git_sha": git_sha,
        }
        registry_entries.append(meta)

        # Se for o champion default, atualiza também model_metadata.json legado
        if candidate["role"] == "champion":
            settings.model_metadata_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    registry_path = settings.model_dir / "registry.json"
    registry_data = {
        "active_champion": "churn-xgboost",
        "updated_at": datetime.now(UTC).isoformat(),
        "models": registry_entries,
    }
    registry_path.write_text(json.dumps(registry_data, indent=2), encoding="utf-8")
    print(f"[REGISTRY] Model Registry salvo em: {registry_path}")

    return registry_data


train_all_candidates = train

if __name__ == "__main__":
    train()
