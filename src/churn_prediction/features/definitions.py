from enum import Enum

from pydantic import BaseModel, Field


class FeatureType(str, Enum):
    INT = "INT"
    FLOAT = "FLOAT"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"


class FeatureSourceType(str, Enum):
    BATCH = "BATCH"
    STREAM = "STREAM"


class FeatureField(BaseModel):
    """Definição de uma feature individual no catálogo da Feature Store."""
    name: str
    dtype: FeatureType
    description: str
    default_value: int | float | str | bool | None = None


class FeatureViewMetadata(BaseModel):
    """Metadados de uma Feature View para governança e orquestração."""
    name: str
    entity_key: str = "customer_id"
    source_type: FeatureSourceType
    ttl_seconds: int = Field(default=86400 * 30, description="Tempo de vida útil das features")
    description: str
    features: list[FeatureField]


# ==============================================================================
# Catálogo Canônico de Feature Views (Feast Architecture)
# ==============================================================================

CUSTOMER_DEMOGRAPHIC_FV = FeatureViewMetadata(
    name="customer_demographic_features",
    entity_key="customer_id",
    source_type=FeatureSourceType.BATCH,
    ttl_seconds=86400 * 30,
    description="Features cadastrais e contratuais originadas do Data Warehouse / CRM",
    features=[
        FeatureField(name="SeniorCitizen", dtype=FeatureType.INT, description="Indicador de cliente idoso (0 ou 1)", default_value=0),
        FeatureField(name="Partner", dtype=FeatureType.STRING, description="Possui cônjuge (Yes/No)", default_value="No"),
        FeatureField(name="Dependents", dtype=FeatureType.STRING, description="Possui dependentes (Yes/No)", default_value="No"),
        FeatureField(name="Contract", dtype=FeatureType.STRING, description="Tipo de contrato (Month-to-month, One year, Two year)", default_value="Month-to-month"),
        FeatureField(name="PaperlessBilling", dtype=FeatureType.STRING, description="Fatura digital (Yes/No)", default_value="Yes"),
        FeatureField(name="PaymentMethod", dtype=FeatureType.STRING, description="Método de pagamento", default_value="Electronic check"),
    ],
)

CUSTOMER_FINANCIAL_FV = FeatureViewMetadata(
    name="customer_financial_features",
    entity_key="customer_id",
    source_type=FeatureSourceType.BATCH,
    ttl_seconds=86400 * 30,
    description="Features de faturamento, tempo de permanência e encargos mensais",
    features=[
        FeatureField(name="tenure", dtype=FeatureType.INT, description="Meses de relacionamento com a operadora", default_value=1),
        FeatureField(name="MonthlyCharges", dtype=FeatureType.FLOAT, description="Valor mensal faturado (R$)", default_value=70.0),
        FeatureField(name="TotalCharges", dtype=FeatureType.FLOAT, description="Valor total faturado acumulado (R$)", default_value=70.0),
    ],
)

CUSTOMER_REALTIME_STREAM_FV = FeatureViewMetadata(
    name="customer_realtime_stream_features",
    entity_key="customer_id",
    source_type=FeatureSourceType.STREAM,
    ttl_seconds=86400 * 7,
    description="Features dinâmicas em tempo real computadas pelo Flink Window Processor (M12)",
    features=[
        FeatureField(name="avg_latency_15min", dtype=FeatureType.FLOAT, description="Latência média dos últimos 15 min (ms)", default_value=20.0),
        FeatureField(name="avg_packet_loss_15min", dtype=FeatureType.FLOAT, description="Perda média de pacotes nos últimos 15 min (%)", default_value=0.0),
        FeatureField(name="disconnect_count_1h", dtype=FeatureType.INT, description="Total de quedas de conexão na última 1h", default_value=0),
        FeatureField(name="failed_payment_count_24h", dtype=FeatureType.INT, description="Tentativas de cobrança recusadas nas últimas 24h", default_value=0),
        FeatureField(name="negative_crm_count_7d", dtype=FeatureType.INT, description="Reclamações críticas no SAC/WhatsApp nos últimos 7d", default_value=0),
        FeatureField(name="avg_sentiment_7d", dtype=FeatureType.FLOAT, description="Sentimento médio dos contatos nos últimos 7d (-1.0 a +1.0)", default_value=0.0),
        FeatureField(name="realtime_instability_score", dtype=FeatureType.FLOAT, description="Índice composto de volatilidade e risco em streaming", default_value=0.0),
    ],
)

ALL_FEATURE_VIEWS: list[FeatureViewMetadata] = [
    CUSTOMER_DEMOGRAPHIC_FV,
    CUSTOMER_FINANCIAL_FV,
    CUSTOMER_REALTIME_STREAM_FV,
]
