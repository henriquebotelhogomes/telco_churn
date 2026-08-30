import json
import time
import uuid
from typing import Any

from sqlalchemy import update

from churn_prediction.db.models import ModelTrainingJob, utc_now
from churn_prediction.db.session import get_sessionmaker
from churn_prediction.models.registry import model_manager
from churn_prediction.models.train import train_all_candidates


class ContinuousTrainingPipeline:
    """
    Orquestrador de Continuous Training (CT) automatizado & Self-Healing Pipeline.
    Treina, avalia, valida Quality Gates e atualiza o Model Registry de forma assíncrona.
    """

    async def start_job(
        self,
        trigger_type: str = "manual_api",
        auto_promote: bool = False,
    ) -> str:
        """Cria e persiste o job com status RUNNING e retorna o job_id."""
        job_id = f"ct-job-{uuid.uuid4().hex[:10]}"
        champion_before = model_manager.active_champion

        session_maker = get_sessionmaker()
        async with session_maker() as session:
            job = ModelTrainingJob(
                job_id=job_id,
                trigger_type=trigger_type,
                status="RUNNING",
                champion_before=champion_before,
                champion_after=champion_before,
                details_json=json.dumps({"auto_promote": auto_promote}),
            )
            session.add(job)
            await session.commit()

        return job_id

    async def execute_job(
        self,
        job_id: str,
        trigger_type: str = "manual_api",
        auto_promote: bool = False,
    ) -> dict[str, Any]:
        """Executa o pipeline completo de retreino, benchmarking e promoção."""
        t0 = time.perf_counter()
        champion_before = model_manager.active_champion

        try:
            # 1. Executa retreino dos modelos candidatos
            registry_data = train_all_candidates()

            # 2. Recarrega os modelos treinados em memoria
            model_manager.discover_models()

            # 3. Identifica o melhor candidato baseado em PR-AUC
            models = registry_data.get("models", [])
            if not models:
                raise RuntimeError("Nenhum modelo foi gerado durante o retreino.")

            best_candidate = max(models, key=lambda m: m["metrics"]["pr_auc"])
            best_name = best_candidate["model_name"]
            best_pr_auc = best_candidate["metrics"]["pr_auc"]

            # Encontra métrica do champion atual
            current_champ_item = next(
                (m for m in models if m["model_name"] == champion_before), best_candidate
            )
            current_pr_auc = current_champ_item["metrics"]["pr_auc"]
            improvement = round(best_pr_auc - current_pr_auc, 4)

            # 4. Quality Gate: PR-AUC do melhor candidato deve ser superior ou tolerância de 0.005
            gate_passed = best_pr_auc >= (current_pr_auc - 0.005)
            status = "SUCCESS" if gate_passed else "REJECTED_BY_GATE"

            champion_after = champion_before
            if gate_passed and auto_promote and best_name != champion_before:
                model_manager.promote_to_champion(best_name)
                champion_after = best_name

            duration = round(time.perf_counter() - t0, 2)

            details = {
                "auto_promote": auto_promote,
                "gate_passed": gate_passed,
                "best_candidate": best_name,
                "best_pr_auc": best_pr_auc,
                "previous_champion_pr_auc": current_pr_auc,
                "all_candidates": [
                    {
                        "model_name": m["model_name"],
                        "algo": m["algo"],
                        "roc_auc": m["metrics"]["roc_auc"],
                        "pr_auc": m["metrics"]["pr_auc"],
                        "latency_ms": m["metrics"]["latency_ms"],
                    }
                    for m in models
                ],
            }

            # 4. Atualiza o registro do job no banco de dados
            session_maker = get_sessionmaker()
            async with session_maker() as session:
                stmt = (
                    update(ModelTrainingJob)
                    .where(ModelTrainingJob.job_id == job_id)
                    .values(
                        status=status,
                        champion_after=champion_after,
                        best_candidate=best_name,
                        metric_improvement=improvement,
                        details_json=json.dumps(details),
                        completed_at=utc_now(),
                        duration_seconds=duration,
                    )
                )
                await session.execute(stmt)
                await session.commit()

            return {
                "job_id": job_id,
                "status": status,
                "duration_seconds": duration,
                "champion_before": champion_before,
                "champion_after": champion_after,
                "best_candidate": best_name,
                "metric_improvement": improvement,
                "details": details,
            }

        except Exception as e:
            duration = round(time.perf_counter() - t0, 2)
            session_maker = get_sessionmaker()
            async with session_maker() as session:
                stmt = (
                    update(ModelTrainingJob)
                    .where(ModelTrainingJob.job_id == job_id)
                    .values(
                        status="FAILED",
                        details_json=json.dumps({"error": str(e)}),
                        completed_at=utc_now(),
                        duration_seconds=duration,
                    )
                )
                await session.execute(stmt)
                await session.commit()

            return {
                "job_id": job_id,
                "status": "FAILED",
                "duration_seconds": duration,
                "error": str(e),
            }


ct_pipeline = ContinuousTrainingPipeline()
