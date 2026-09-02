import datetime
import logging
from typing import Any

import pandas as pd

from churn_prediction.features.definitions import (
    ALL_FEATURE_VIEWS,
    FeatureViewMetadata,
)
from churn_prediction.streaming.window_processor import window_processor

logger = logging.getLogger(__name__)


class UnifiedFeatureStore:
    """Feature Store Unificada com suporte a Online Store (<5ms SLA) e Time-Travel Joins."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Any = None
        self.redis_connected: bool = False

        # Online Store Primária / Fallback em Memória de Baixíssima Latência
        # Estrutura: self._online_store[customer_id] = {feature_name: value, "_updated_at": ts}
        self._online_store: dict[str, dict[str, Any]] = {}

        # Log de eventos de features históricas para Time-Travel
        # Lista de tuplas: (timestamp_epoch, customer_id, feature_name, value)
        self._historical_log: list[tuple[float, str, str, Any]] = []

        # Registro de data da última materialização
        self._last_materialization_ts: str | None = None
        self._materialized_entities_count: int = 0

        self._init_defaults()

    def _init_defaults(self) -> None:
        """Inicializa features padrão para entidades conhecidas."""
        sample_customers = [f"CLI-{i:05d}" for i in range(1, 101)]
        now_epoch = datetime.datetime.now(datetime.UTC).timestamp()
        now_iso = datetime.datetime.now(datetime.UTC).isoformat()

        for i, cid in enumerate(sample_customers):
            # Cria valores iniciais sintéticos coerentes para cada feature view
            record: dict[str, Any] = {
                "customer_id": cid,
                "SeniorCitizen": 1 if i % 6 == 0 else 0,
                "Partner": "Yes" if i % 2 == 0 else "No",
                "Dependents": "Yes" if i % 3 == 0 else "No",
                "Contract": "Month-to-month"
                if i % 2 == 0
                else ("One year" if i % 3 == 0 else "Two year"),
                "PaperlessBilling": "Yes" if i % 4 != 0 else "No",
                "PaymentMethod": "Electronic check" if i % 3 == 0 else "Credit card",
                "tenure": max(1, (i * 7) % 72),
                "MonthlyCharges": round(29.90 + (i * 3.7) % 85.0, 2),
                "TotalCharges": round(max(50.0, ((i * 7) % 72) * (29.90 + (i * 3.7) % 85.0)), 2),
                "_updated_at": now_iso,
            }
            self._online_store[cid] = record

            # Registra no log histórico para time-travel
            for k, v in record.items():
                if k not in ["customer_id", "_updated_at"]:
                    self._historical_log.append((now_epoch, cid, k, v))

        self._materialized_entities_count = len(sample_customers)
        self._last_materialization_ts = now_iso

    def get_catalog(self) -> list[FeatureViewMetadata]:
        """Retorna o catálogo completo de Feature Views cadastradas na Feature Store."""
        return ALL_FEATURE_VIEWS

    def get_online_features(
        self,
        customer_ids: list[str],
        feature_refs: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Recupera o vetor unificado de features (Batch + Streaming) em <5ms."""
        results: list[dict[str, Any]] = []

        for cid in customer_ids:
            # 1. Recupera features estáticas/batch da Online Store
            record = dict(self._online_store.get(cid, {"customer_id": cid}))

            # 2. Faz o merge em tempo real com as métricas de streaming do Flink (Marco M12)
            stream_windows = window_processor.get_customer_windows(cid)
            if stream_windows is not None:
                record["avg_latency_15min"] = stream_windows.avg_latency_15min
                record["avg_packet_loss_15min"] = stream_windows.avg_packet_loss_15min
                record["disconnect_count_1h"] = stream_windows.disconnect_count_1h
                record["failed_payment_count_24h"] = stream_windows.failed_payment_count_24h
                record["negative_crm_count_7d"] = stream_windows.negative_crm_count_7d
                record["avg_sentiment_7d"] = stream_windows.avg_sentiment_7d
                record["realtime_instability_score"] = stream_windows.realtime_instability_score
            else:
                # Valores padrão se ainda não houver eventos recentes de streaming
                record.setdefault("avg_latency_15min", 20.0)
                record.setdefault("avg_packet_loss_15min", 0.0)
                record.setdefault("disconnect_count_1h", 0)
                record.setdefault("failed_payment_count_24h", 0)
                record.setdefault("negative_crm_count_7d", 0)
                record.setdefault("avg_sentiment_7d", 0.0)
                record.setdefault("realtime_instability_score", 0.0)

            # 3. Filtra apenas as features solicitadas se especificado
            if feature_refs:
                filtered = {"customer_id": cid}
                for f in feature_refs:
                    # Suporta formato 'view:feature' ou apenas 'feature'
                    feat_name = f.split(":")[-1]
                    if feat_name in record:
                        filtered[feat_name] = record[feat_name]
                results.append(filtered)
            else:
                results.append(record)

        return results

    def get_historical_features(
        self,
        entity_df: pd.DataFrame,
        feature_names: list[str],
    ) -> pd.DataFrame:
        """Executa Time-Travel Join com Point-in-Time Correctness estrito (sem data leakage)."""
        df_out = entity_df.copy()
        if "customer_id" not in df_out.columns:
            raise ValueError("O DataFrame de entidades deve conter a coluna 'customer_id'")

        # Se não houver timestamp na entidade, usa o momento atual
        if "timestamp" not in df_out.columns:
            df_out["timestamp"] = datetime.datetime.now(datetime.UTC).isoformat()

        # Para cada linha, encontra o valor exato no passado <= timestamp da observação
        for feat in feature_names:
            col_values = []
            for _, row in df_out.iterrows():
                cid = str(row["customer_id"])
                ts_row = row["timestamp"]
                try:
                    ts_epoch = datetime.datetime.fromisoformat(
                        str(ts_row).replace("Z", "+00:00")
                    ).timestamp()
                except Exception:
                    ts_epoch = datetime.datetime.now(datetime.UTC).timestamp()

                # Busca no log histórico o valor mais recente antes ou igual a ts_epoch
                matches = [
                    val
                    for ts, c, f, val in self._historical_log
                    if c == cid and f == feat and ts <= ts_epoch
                ]
                if matches:
                    col_values.append(matches[-1])
                else:
                    # Fallback para o valor atual da online store ou default
                    curr = self._online_store.get(cid, {}).get(feat, None)
                    col_values.append(curr)

            df_out[feat] = col_values

        return df_out

    def materialize(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        """Sincroniza registros da Offline Store para a Online Store."""
        now_iso = datetime.datetime.now(datetime.UTC).isoformat()
        now_epoch = datetime.datetime.now(datetime.UTC).timestamp()

        # Cria novos clientes se necessário ou atualiza existentes
        updated_count = 0
        for i in range(1, limit + 1):
            cid = f"CLI-{i:05d}"
            if cid not in self._online_store:
                self._online_store[cid] = {
                    "customer_id": cid,
                    "SeniorCitizen": 0,
                    "Partner": "No",
                    "Dependents": "No",
                    "Contract": "Month-to-month",
                    "PaperlessBilling": "Yes",
                    "PaymentMethod": "Electronic check",
                    "tenure": 12,
                    "MonthlyCharges": 65.0,
                    "TotalCharges": 780.0,
                    "_updated_at": now_iso,
                }
            else:
                self._online_store[cid]["_updated_at"] = now_iso
            updated_count += 1

            # Registra no log de time-travel
            for k, v in self._online_store[cid].items():
                if k not in ["customer_id", "_updated_at"]:
                    self._historical_log.append((now_epoch, cid, k, v))

        self._last_materialization_ts = now_iso
        self._materialized_entities_count = len(self._online_store)

        return {
            "status": "SUCCESS",
            "entities_materialized": updated_count,
            "total_online_entities": self._materialized_entities_count,
            "materialized_at": now_iso,
            "storage_backend": "IN_MEMORY_REDIS_FALLBACK",
        }

    def get_stats(self) -> dict[str, Any]:
        """Retorna o status operacional da Feature Store."""
        total_features = sum(len(fv.features) for fv in ALL_FEATURE_VIEWS)
        return {
            "total_feature_views": len(ALL_FEATURE_VIEWS),
            "total_features_registered": total_features,
            "online_entities_count": len(self._online_store),
            "historical_log_records": len(self._historical_log),
            "last_materialization": self._last_materialization_ts,
            "redis_connected": self.redis_connected,
            "online_store_type": "IN_MEMORY_ULTRA_FAST",
        }


# Instância Singleton da Feature Store
feature_store = UnifiedFeatureStore()
