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

    # Parâmetros do modelo
    random_state: int = 42
    test_size: float = 0.2

    # Padrão Pydantic V2 para configurações (substitui a antiga 'class Config:')
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Instância global para ser importada em outros módulos
settings = Settings()
