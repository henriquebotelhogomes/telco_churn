import json
import subprocess
from datetime import UTC, datetime

import joblib
import sklearn
import xgboost
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


def train() -> None:
    """
    Pipeline completo de treinamento: carrega dados, treina e salva o modelo.
    """
    print("🚀 Iniciando pipeline de treinamento...")

    # 1. Carregar os dados
    print(f"📂 Carregando dados de: {settings.raw_data_path}")
    X, y = load_and_split_data(settings.raw_data_path)

    # 2. Divisão Treino/Teste
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=settings.test_size, random_state=settings.random_state, stratify=y
    )
    print(f"✂️ Dados divididos: {len(X_train)} treino | {len(X_test)} teste")

    # 3. Construir o Pipeline Final (Pré-processamento + Modelo)
    # Usamos scale_pos_weight para lidar com o desbalanceamento (Churn = Yes é minoria)
    pos_weight = (len(y_train) - y_train.sum()) / y_train.sum()

    model_pipeline = Pipeline(
        steps=[
            ("preprocessing", get_preprocessing_pipeline()),
            (
                "classifier",
                XGBClassifier(
                    random_state=settings.random_state,
                    scale_pos_weight=pos_weight,
                    eval_metric="logloss",
                ),
            ),
        ]
    )

    # 4. Treinamento
    print("🧠 Treinando o modelo XGBoost...")
    model_pipeline.fit(X_train, y_train)

    # 5. Avaliação
    print("📈 Avaliando o modelo no conjunto de teste...")
    metrics = evaluate_model(model_pipeline, X_test, y_test)

    # 6. Salvar o artefato
    settings.model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model_pipeline, settings.model_path)
    print(f"✅ Modelo salvo com sucesso em: {settings.model_path}")

    # 7. Metadados do modelo (expostos em GET /api/v1/model/info)
    metadata = {
        "model_name": "churn-xgboost",
        "version": "1.0.0",
        "algo": "XGBoost",
        "trained_at": datetime.now(UTC).isoformat(),
        "framework_versions": {
            "xgboost": xgboost.__version__,
            "scikit-learn": sklearn.__version__,
        },
        "dataset": {
            "path": str(settings.raw_data_path),
            "rows": int(len(X)),
            "columns": [str(coluna) for coluna in X.columns],
            "positive_rate": round(float(y.mean()), 4),
        },
        "split": {
            "test_size": settings.test_size,
            "random_state": settings.random_state,
        },
        "metrics": metrics,
        "risk_thresholds": settings.risk_thresholds,
        "artifact": str(settings.model_path),
        "git_sha": _git_sha(),
    }
    settings.model_metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"🪪 Metadados salvos em: {settings.model_metadata_path}")


if __name__ == "__main__":
    train()
