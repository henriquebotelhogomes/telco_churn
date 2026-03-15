from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class TotalChargesCleaner(BaseEstimator, TransformerMixin):
    """
    Transformer customizado para limpar a coluna TotalCharges.
    Converte espaços vazios para NaN e transforma em float.
    """

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "TotalChargesCleaner":
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X_copy = X.copy()
        if "TotalCharges" in X_copy.columns:
            X_copy["TotalCharges"] = pd.to_numeric(
                X_copy["TotalCharges"].replace(" ", np.nan), errors="coerce"
            )
        return X_copy


def get_preprocessing_pipeline() -> Pipeline:
    """
    Constrói e retorna o pipeline completo de pré-processamento do scikit-learn.
    """
    numeric_features = ["tenure", "MonthlyCharges", "TotalCharges"]

    categorical_features = [
        "gender",
        "SeniorCitizen",
        "Partner",
        "Dependents",
        "PhoneService",
        "MultipleLines",
        "InternetService",
        "OnlineSecurity",
        "OnlineBackup",
        "DeviceProtection",
        "TechSupport",
        "StreamingTV",
        "StreamingMovies",
        "Contract",
        "PaperlessBilling",
        "PaymentMethod",
    ]

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", drop="if_binary")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop",
    )

    full_pipeline = Pipeline(
        steps=[
            ("cleaner", TotalChargesCleaner()),
            ("preprocessor", preprocessor),
        ]
    )

    return full_pipeline


def load_and_split_data(filepath: str | Path) -> tuple[pd.DataFrame, pd.Series]:
    """
    Carrega o CSV e separa as features (X) do target (y).
    """
    df = pd.read_csv(filepath)

    y = df["Churn"].map({"Yes": 1, "No": 0}).astype(int)
    X = df.drop(columns=["Churn"])

    return X, y
