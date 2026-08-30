import asyncio
import datetime
import json
import random
from typing import Any

from sqlalchemy import func, select

from churn_prediction.db.models import (
    CustomerOutcome,
    CustomerPrediction,
    RetentionPlaybookAction,
)
from churn_prediction.db.session import get_sessionmaker, init_db

PLAYBOOKS = [
    (
        "MIGRAÇÃO_CONTRATO_ANUAL",
        "Oferecer 15% de desconto no plano anual com inclusão de Suporte Técnico.",
    ),
    (
        "CROSS_SELL_PROTECAO",
        "Oferecer combo de Suporte Técnico + Segurança Online com 50% de desconto.",
    ),
    (
        "AUTOMATIZACAO_PAGAMENTO",
        "Oferecer R$ 10 de crédito na fatura para ativação de Débito Automático / Cartão.",
    ),
    (
        "DESCONTO_RETENCAO_EMERGENCIAL",
        "Aplicar desconto de 15% nas próximas 3 faturas sem alteração de plano.",
    ),
]


async def seed_historical_data(force: bool = False) -> dict[str, Any]:
    """Popula o banco com histórico de 6 meses para demonstração imediata no dashboard."""
    await init_db()
    session_maker = get_sessionmaker()

    async with session_maker() as session:
        # Verifica se já tem dados
        count_res = await session.execute(select(func.count(CustomerPrediction.id)))
        total_existente = count_res.scalar() or 0
        if total_existente > 0 and not force:
            return {"status": "already_seeded", "predictions": total_existente}

        now = datetime.datetime.now(datetime.UTC)
        random.seed(42)

        predictions: list[CustomerPrediction] = []
        actions: list[RetentionPlaybookAction] = []
        outcomes: list[CustomerOutcome] = []

        # Gera dados nos últimos 6 meses (semana a semana)
        for days_ago in range(180, 0, -3):
            data_ponto = now - datetime.timedelta(days=days_ago, hours=random.randint(1, 23))

            # Gera 5 a 15 predições por ponto temporal
            num_preds = random.randint(5, 12)
            for i in range(num_preds):
                cust_id = f"CUST-{random.randint(1000, 9999)}"
                p = random.betavariate(1.8, 3.5)  # distribuição realista
                if p >= 0.8:
                    nivel = "Crítico"
                elif p >= 0.6:
                    nivel = "Alto"
                elif p >= 0.3:
                    nivel = "Médio"
                else:
                    nivel = "Baixo"

                monthly = random.uniform(30.0, 110.0)
                mrr = monthly * p if nivel in ("Alto", "Crítico") else 0.0

                playbook_escolhido, desc = random.choice(PLAYBOOKS)

                pred = CustomerPrediction(
                    customer_id=cust_id,
                    prediction=int(p >= 0.5),
                    probability=round(p, 4),
                    risk_level=nivel,
                    mrr_at_risk=round(mrr, 2),
                    recommended_action=playbook_escolhido,
                    top_drivers_json=json.dumps(
                        [
                            {
                                "fator": "Tipo de Contrato",
                                "impacto": "+25%",
                                "direcao": "aumenta_risco",
                            },
                            {
                                "fator": "Serviço de Internet",
                                "impacto": "+18%",
                                "direcao": "aumenta_risco",
                            },
                        ]
                    ),
                    model_version="v1.0.0",
                    created_at=data_ponto,
                )
                predictions.append(pred)

                # Se o risco for alto ou crítico, simula intervenção de retenção em 60% dos casos
                if nivel in ("Alto", "Crítico") and random.random() < 0.60:
                    action_time = data_ponto + datetime.timedelta(hours=random.randint(2, 48))
                    action = RetentionPlaybookAction(
                        customer_id=cust_id,
                        playbook=playbook_escolhido,
                        description=desc,
                        discount_pct=15.0 if "DESCONTO" in playbook_escolhido else 0.0,
                        estimated_risk_reduction=round(random.uniform(0.20, 0.45), 3),
                        expected_annual_savings=round(monthly * 12 * 0.30, 2),
                        applied_by=random.choice(["analyst_bruno", "analyst_carla", "system_auto"]),
                        status=random.choice(["accepted", "accepted", "accepted", "rejected"]),
                        created_at=action_time,
                    )
                    actions.append(action)

                    # Desfecho observado após 30 a 60 dias da ação
                    if days_ago > 30:
                        outcome_time = action_time + datetime.timedelta(days=random.randint(30, 45))
                        # Playbook aceito tem 78% de taxa de retenção (churn = 0)
                        churn = (
                            0
                            if (action.status == "accepted" and random.random() < 0.78)
                            else (1 if random.random() < 0.65 else 0)
                        )
                        outcome = CustomerOutcome(
                            customer_id=cust_id,
                            churn_occurred=churn,
                            observed_months=1,
                            actual_revenue_saved=round(monthly * 12, 2) if churn == 0 else 0.0,
                            outcome_date=outcome_time,
                        )
                        outcomes.append(outcome)

        session.add_all(predictions)
        session.add_all(actions)
        session.add_all(outcomes)
        await session.commit()

        return {
            "status": "seeded_successfully",
            "predictions_count": len(predictions),
            "actions_count": len(actions),
            "outcomes_count": len(outcomes),
        }


if __name__ == "__main__":
    resultado = asyncio.run(seed_historical_data(force=True))
    print("Seed concluído:", resultado)
