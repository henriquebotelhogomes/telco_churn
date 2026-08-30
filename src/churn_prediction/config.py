from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Define a raiz do projeto dinamicamente
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Configurações globais do projeto."""

    # Caminhos de dados
    data_path: Path = PROJECT_ROOT / "data"
    raw_data_path: Path = data_path / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"

    # Caminhos de modelos
    model_dir: Path = PROJECT_ROOT / "models"
    model_path: Path = model_dir / "churn_model_pipeline.joblib"
    model_metadata_path: Path = model_dir / "model_metadata.json"

    # Parâmetros do modelo
    random_state: int = 42
    test_size: float = 0.2

    # RetainIQ - Níveis de risco (centralizados, nunca hard-coded na API)
    # Baixo: p < 0.30 | Médio: 0.30 ≤ p < 0.60 | Alto: 0.60 ≤ p < 0.80 | Crítico: p ≥ 0.80
    # PRD exige nome RISK_THRESHOLDS (uppercase) — mantido como alias
    risk_thresholds: dict[str, float] = {
        "baixo": 0.30,
        "medio": 0.60,
        "alto": 0.80,
        "critico": 0.80,
    }
    RISK_THRESHOLDS: dict[str, float] = {
        "baixo": 0.30,
        "medio": 0.60,
        "alto": 0.80,
        "critico": 0.80,
    }

    # RetainIQ - Drift & observabilidade
    ring_buffer_maxlen: int = 5000
    drift_ttl_seconds: int = 3600
    drift_min_samples: int = 50
    cors_origins: list[str] = []
    api_key_enabled: bool = False
    api_key: str | None = None

    # Padrão Pydantic V2 para configurações (substitui a antiga 'class Config:')
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


# Instância global para ser importada em outros módulos
settings = Settings()
