import json
import time
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

from churn_prediction.config import settings


def _risk_level(prob: float) -> str:
    if prob >= settings.risk_thresholds.get("critico", 0.8):
        return "Crítico"
    if prob >= settings.risk_thresholds.get("alto", 0.6):
        return "Alto"
    if prob >= settings.risk_thresholds.get("medio", 0.3):
        return "Médio"
    return "Baixo"


class ModelManager:
    """
    Gerenciador central do Model Registry, Shadow Scoring e Champion/Challenger Deployment.
    """

    def __init__(self, registry_file: Path | None = None) -> None:
        self.registry_file = registry_file or (settings.model_dir / "registry.json")
        self._models: dict[str, Pipeline] = {}
        self._active_champion: str = "churn-xgboost"
        self._registry_data: dict[str, Any] = {"active_champion": "churn-xgboost", "models": []}
        # Buffer circular de telemetria de shadow scoring (últimas 1000 inferências)
        self._shadow_buffer: deque[dict[str, Any]] = deque(maxlen=1000)

    def initialize(self) -> None:
        """Carrega os metadados do registry e pré-carrega os pipelines em memória."""
        if self.registry_file.exists():
            try:
                self._registry_data = json.loads(self.registry_file.read_text(encoding="utf-8"))
                self._active_champion = self._registry_data.get("active_champion", "churn-xgboost")
            except Exception as e:
                print(f"[REGISTRY] Aviso ao ler registry.json: {e}")

        # Carrega todos os modelos listados no registry
        for item in self._registry_data.get("models", []):
            name = item["model_name"]
            art_path = Path(item["artifact"])
            if art_path.exists():
                try:
                    self._models[name] = joblib.load(art_path)
                    print(f"[REGISTRY] Modelo '{name}' carregado em memoria.")
                except Exception as e:
                    print(f"[REGISTRY] Falha ao carregar artefato '{art_path}': {e}")

        # Fallback se o registry estiver vazio ou faltar champion
        if not self._models and settings.model_path.exists():
            try:
                self._models["churn-xgboost"] = joblib.load(settings.model_path)
                self._active_champion = "churn-xgboost"
            except Exception as e:
                print(f"[REGISTRY] Falha no fallback do champion: {e}")

    @property
    def active_champion(self) -> str:
        return self._active_champion

    def discover_models(self) -> None:
        """Alias para initialize() recarregando modelos e metadados."""
        self.initialize()

    def get_champion(self) -> tuple[str, Pipeline | None]:
        """Retorna o nome e o pipeline do Champion ativo atual."""
        pipeline = self._models.get(self._active_champion)
        if pipeline is None and self._models:
            # Fallback para o primeiro modelo disponível
            primeiro_nome = next(iter(self._models))
            return primeiro_nome, self._models[primeiro_nome]
        return self._active_champion, pipeline

    def get_model(self, name: str) -> Pipeline | None:
        return self._models.get(name)

    def list_models(self) -> dict[str, Any]:
        """Retorna o catálogo completo de modelos com seus papéis atualizados."""
        models_list = []
        for m in self._registry_data.get("models", []):
            item = dict(m)
            # Atualiza o papel dinâmico de acordo com o active_champion
            if item["model_name"] == self._active_champion:
                item["role"] = "champion"
            elif item["role"] == "champion":
                item["role"] = "challenger"
            models_list.append(item)

        return {
            "active_champion": self._active_champion,
            "total_models": len(models_list),
            "updated_at": self._registry_data.get("updated_at"),
            "models": models_list,
        }

    def promote_to_champion(self, model_name: str) -> dict[str, Any]:
        """Promove um modelo para Champion em tempo de execução sem reiniciar a API."""
        if model_name not in self._models:
            raise ValueError(f"Modelo '{model_name}' não encontrado no registry.")

        old_champion = self._active_champion
        self._active_champion = model_name
        self._registry_data["active_champion"] = model_name
        self._registry_data["updated_at"] = datetime.now(UTC).isoformat()

        # Atualiza os papéis no json
        for m in self._registry_data.get("models", []):
            if m["model_name"] == model_name:
                m["role"] = "champion"
            elif m["model_name"] == old_champion:
                m["role"] = "challenger"

        # Persiste a alteração no disco
        try:
            self.registry_file.write_text(
                json.dumps(self._registry_data, indent=2), encoding="utf-8"
            )
        except Exception as e:
            print(f"[REGISTRY] Aviso ao persistir promocao: {e}")

        return {
            "status": "promoted_successfully",
            "previous_champion": old_champion,
            "new_champion": model_name,
            "promoted_at": self._registry_data["updated_at"],
        }

    def record_shadow_scoring(
        self,
        df_input: pd.DataFrame,
        champion_prob: float,
        champion_risk: str,
    ) -> None:
        """
        Executa pontuação não-bloqueante (Shadow) nos Challengers e armazena telemetria.
        """
        challenger_scores: dict[str, dict[str, Any]] = {}
        agreement_count = 0
        challenger_total = 0

        for name, pipe in self._models.items():
            if name == self._active_champion:
                continue

            t0 = time.perf_counter()
            try:
                prob = float(pipe.predict_proba(df_input)[0, 1])
                lat_ms = (time.perf_counter() - t0) * 1000
                risk = _risk_level(prob)
                is_agreement = risk == champion_risk
                if is_agreement:
                    agreement_count += 1
                challenger_total += 1

                challenger_scores[name] = {
                    "probability": round(prob, 4),
                    "risk_level": risk,
                    "latency_ms": round(lat_ms, 3),
                    "agrees_with_champion": is_agreement,
                    "prob_difference": round(abs(prob - champion_prob), 4),
                }
            except Exception:
                pass

        if challenger_total > 0:
            concordance_rate = (agreement_count / challenger_total) * 100
            self._shadow_buffer.append(
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "champion_name": self._active_champion,
                    "champion_prob": round(champion_prob, 4),
                    "champion_risk": champion_risk,
                    "concordance_rate_pct": round(concordance_rate, 1),
                    "challengers": challenger_scores,
                }
            )

    def get_shadow_telemetry(self) -> dict[str, Any]:
        """Calcula métricas agregadas de Shadow Scoring em tempo real."""
        if not self._shadow_buffer:
            return {
                "total_shadow_scored": 0,
                "overall_agreement_rate_pct": 100.0,
                "avg_concordance_pct": 100.0,
                "recent_samples_count": 0,
                "model_comparisons": [],
                "recent_events": [],
            }

        total = len(self._shadow_buffer)
        concordances = [item["concordance_rate_pct"] for item in self._shadow_buffer]
        avg_conc = sum(concordances) / total if total > 0 else 100.0

        # Estatísticas por challenger
        stats_by_model: dict[str, list[dict[str, Any]]] = {}
        for entry in self._shadow_buffer:
            for mod_name, res in entry.get("challengers", {}).items():
                if mod_name not in stats_by_model:
                    stats_by_model[mod_name] = []
                stats_by_model[mod_name].append(res)

        model_comparisons = []
        for mod_name, scores in stats_by_model.items():
            qtd = len(scores)
            agree_qtd = sum(1 for s in scores if s["agrees_with_champion"])
            taxa_conc = (agree_qtd / qtd * 100) if qtd > 0 else 100.0
            avg_lat = sum(s["latency_ms"] for s in scores) / qtd if qtd > 0 else 0.0
            avg_diff = sum(s["prob_difference"] for s in scores) / qtd if qtd > 0 else 0.0

            model_comparisons.append(
                {
                    "model_name": mod_name,
                    "total_samples": qtd,
                    "agreement_rate_pct": round(taxa_conc, 1),
                    "avg_latency_ms": round(avg_lat, 3),
                    "avg_prob_diff": round(avg_diff, 4),
                }
            )

        return {
            "total_shadow_scored": total,
            "avg_concordance_pct": round(avg_conc, 1),
            "recent_samples_count": total,
            "model_comparisons": model_comparisons,
            "recent_events": list(self._shadow_buffer)[-10:],
        }


# Instância global do ModelManager
model_manager = ModelManager()
