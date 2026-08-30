import datetime
import json
from typing import Any

from sqlalchemy import desc, func, select

from churn_prediction.db.models import (
    CustomerOutcome,
    CustomerPrediction,
    ModelTrainingJob,
    RetentionPlaybookAction,
)
from churn_prediction.db.session import get_sessionmaker
from churn_prediction.models.registry import model_manager


class ExecutiveReportGenerator:
    """
    Gerador de Relatórios Executivos C-Level & Dossiês de Retenção Estratégica.
    Consolida métricas financeiras, eficácia de playbooks e governança de MLOps.
    """

    async def get_report_data(self) -> dict[str, Any]:
        """Extrai e agrega todos os dados executivos do banco relacional."""
        session_maker = get_sessionmaker()
        async with session_maker() as session:
            # 1. Predições e Risco
            pred_count_stmt = select(func.count(CustomerPrediction.id))
            pred_count = (await session.execute(pred_count_stmt)).scalar() or 0

            mrr_risk_stmt = select(func.sum(CustomerPrediction.mrr_at_risk))
            total_mrr_risk = (await session.execute(mrr_risk_stmt)).scalar() or 0.0

            high_risk_stmt = select(func.count(CustomerPrediction.id)).where(
                CustomerPrediction.risk_level.in_(["Alto", "Crítico"])
            )
            high_risk_count = (await session.execute(high_risk_stmt)).scalar() or 0

            # 2. Desfecho real (MRR Salvo)
            mrr_saved_stmt = select(func.sum(CustomerOutcome.actual_revenue_saved))
            total_mrr_saved = (await session.execute(mrr_saved_stmt)).scalar() or 0.0

            outcomes_count_stmt = select(func.count(CustomerOutcome.id))
            total_outcomes = (await session.execute(outcomes_count_stmt)).scalar() or 0

            retained_stmt = select(func.count(CustomerOutcome.id)).where(
                CustomerOutcome.churn_occurred == 0
            )
            retained_count = (await session.execute(retained_stmt)).scalar() or 0
            retention_rate = (
                round((retained_count / total_outcomes) * 100, 1) if total_outcomes > 0 else 0.0
            )

            # 3. Eficácia de Playbooks
            pb_stmt = select(
                RetentionPlaybookAction.playbook,
                func.count(RetentionPlaybookAction.id).label("total_applied"),
                func.sum(RetentionPlaybookAction.expected_annual_savings).label("total_savings"),
            ).group_by(RetentionPlaybookAction.playbook)
            pb_rows = (await session.execute(pb_stmt)).all()
            playbooks_summary = [
                {
                    "playbook": r.playbook,
                    "total_applied": r.total_applied,
                    "projected_savings": round(r.total_savings or 0.0, 2),
                }
                for r in pb_rows
            ]

            # 4. Top 10 Clientes em Risco Crítico
            top_risk_stmt = (
                select(CustomerPrediction).order_by(desc(CustomerPrediction.probability)).limit(10)
            )
            top_risk_rows = (await session.execute(top_risk_stmt)).scalars().all()
            top_risk_accounts = []
            for c in top_risk_rows:
                drivers = []
                if c.top_drivers_json:
                    try:
                        parsed = json.loads(c.top_drivers_json)
                        drivers = [d.get("fator", "") for d in parsed[:2]]
                    except Exception:
                        pass

                top_risk_accounts.append(
                    {
                        "customer_id": c.customer_id,
                        "probability_pct": round(c.probability * 100, 1),
                        "risk_level": c.risk_level,
                        "mrr_at_risk": round(c.mrr_at_risk, 2),
                        "recommended_action": c.recommended_action or "Ação de Retenção Padrão",
                        "top_drivers": drivers,
                    }
                )

            # 5. Último job de Continuous Training
            ct_stmt = select(ModelTrainingJob).order_by(desc(ModelTrainingJob.created_at)).limit(1)
            last_ct_job = (await session.execute(ct_stmt)).scalars().first()
            ct_summary = None
            if last_ct_job:
                ct_summary = {
                    "job_id": last_ct_job.job_id,
                    "status": last_ct_job.status,
                    "champion_after": last_ct_job.champion_after,
                    "metric_improvement_pct": round(last_ct_job.metric_improvement * 100, 2),
                    "duration_seconds": last_ct_job.duration_seconds,
                    "completed_at": last_ct_job.completed_at.isoformat()
                    if last_ct_job.completed_at
                    else None,
                }

        champion_name, _ = model_manager.get_champion()

        return {
            "title": "RetainIQ — Executive Retention Dossier",
            "subtitle": "Relatório Estratégico de Prevenção de Churn & Governança de MLOps",
            "generated_at": datetime.datetime.now(datetime.UTC).strftime("%d/%m/%Y %H:%M:%S UTC"),
            "financial_kpis": {
                "total_customers_scored": pred_count,
                "high_risk_customers": high_risk_count,
                "total_mrr_at_risk": round(total_mrr_risk, 2),
                "total_mrr_saved": round(total_mrr_saved, 2),
                "retention_success_rate_pct": retention_rate,
                "roi_estimated": round((total_mrr_saved / (total_mrr_risk * 0.15 + 1.0)) * 100, 1),
            },
            "playbooks_summary": playbooks_summary,
            "top_risk_accounts": top_risk_accounts,
            "mlops_governance": {
                "active_champion": champion_name,
                "models_in_registry": len(model_manager.list_models().get("models", [])),
                "last_continuous_training_job": ct_summary,
            },
        }

    def render_html_dossier(self, data: dict[str, Any]) -> str:
        """Gera um documento HTML completo, responsivo e print-ready para C-Level / PDF."""
        kpis = data["financial_kpis"]
        mlops = data["mlops_governance"]
        playbooks = data["playbooks_summary"]
        accounts = data["top_risk_accounts"]

        playbooks_rows = (
            "".join(
                f"""
            <tr>
                <td style="padding: 10px 14px; font-weight: 600; color: #1e293b;">{p["playbook"]}</td>
                <td style="padding: 10px 14px; text-align: center; color: #475569;">{p["total_applied"]} ações</td>
                <td style="padding: 10px 14px; text-align: right; font-weight: 700; color: #059669;">R$ {p["projected_savings"]:,.2f}</td>
            </tr>
            """
                for p in playbooks
            )
            or "<tr><td colspan='3' style='padding:12px; text-align:center; color:#94a3b8;'>Nenhum playbook aplicado até o momento.</td></tr>"
        )

        accounts_rows = (
            "".join(
                f"""
            <tr>
                <td style="padding: 10px 14px; font-family: monospace; font-weight: 600; color: #0f172a;">{a["customer_id"]}</td>
                <td style="padding: 10px 14px; text-align: center;">
                    <span style="background: {"#fee2e2" if a["probability_pct"] >= 60 else "#fef3c7"}; color: {"#991b1b" if a["probability_pct"] >= 60 else "#92400e"}; padding: 3px 8px; border-radius: 9999px; font-size: 11px; font-weight: 700;">
                        {a["probability_pct"]}% ({a["risk_level"]})
                    </span>
                </td>
                <td style="padding: 10px 14px; text-align: right; font-weight: 700; color: #b91c1c;">R$ {a["mrr_at_risk"]:,.2f}</td>
                <td style="padding: 10px 14px; color: #334155; font-size: 12px;">{", ".join(a["top_drivers"]) or "Múltiplos fatores"}</td>
                <td style="padding: 10px 14px; color: #2563eb; font-size: 12px; font-weight: 600;">{a["recommended_action"]}</td>
            </tr>
            """
                for a in accounts
            )
            or "<tr><td colspan='5' style='padding:12px; text-align:center; color:#94a3b8;'>Nenhuma conta em risco identificada.</td></tr>"
        )

        last_job_html = "Nenhum retreino registrado."
        if mlops.get("last_continuous_training_job"):
            job = mlops["last_continuous_training_job"]
            last_job_html = f"Job <code>{job['job_id']}</code> | Status: <b>{job['status']}</b> | Modelo: <b>{job['champion_after']}</b> | Duração: {job['duration_seconds']}s"

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data["title"]}</title>
    <style>
        @page {{
            margin: 15mm;
            size: A4 portrait;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #0f172a;
            background-color: #f8fafc;
            margin: 0;
            padding: 30px;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            padding: 36px 40px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 20px;
            margin-bottom: 24px;
        }}
        .logo-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            padding: 6px 14px;
            border-radius: 8px;
            font-weight: 800;
            font-size: 14px;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .title {{
            font-size: 22px;
            font-weight: 800;
            color: #0f172a;
            margin: 0 0 4px 0;
        }}
        .subtitle {{
            font-size: 13px;
            color: #64748b;
            margin: 0;
        }}
        .meta-info {{
            text-align: right;
            font-size: 11px;
            color: #64748b;
        }}
        .grid-kpis {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 28px;
        }}
        .kpi-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 14px;
            text-align: center;
        }}
        .kpi-value {{
            font-size: 20px;
            font-weight: 800;
            color: #0f172a;
            margin-top: 4px;
        }}
        .kpi-label {{
            font-size: 11px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .section-title {{
            font-size: 15px;
            font-weight: 700;
            color: #1e293b;
            border-left: 4px solid #4f46e5;
            padding-left: 10px;
            margin: 24px 0 12px 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-bottom: 20px;
        }}
        th {{
            background: #f1f5f9;
            color: #475569;
            font-weight: 700;
            text-align: left;
            padding: 10px 14px;
            border-bottom: 1px solid #cbd5e1;
            font-size: 11px;
            text-transform: uppercase;
        }}
        tr:nth-child(even) {{
            background: #f8fafc;
        }}
        .mlops-box {{
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 8px;
            padding: 14px 18px;
            font-size: 12px;
            color: #166534;
            margin-bottom: 24px;
        }}
        .footer {{
            border-top: 1px solid #e2e8f0;
            padding-top: 16px;
            font-size: 11px;
            color: #94a3b8;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .print-btn {{
            background: #4f46e5;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 12px;
            cursor: pointer;
            display: inline-block;
        }}
        @media print {{
            body {{ background: white; padding: 0; }}
            .container {{ box-shadow: none; border: none; padding: 0; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <div class="logo-badge">RETAINIQ PLATFORM</div>
                <h1 class="title">{data["title"]}</h1>
                <p class="subtitle">{data["subtitle"]}</p>
            </div>
            <div class="meta-info">
                <p><b>Data do Dossiê:</b><br>{data["generated_at"]}</p>
                <button class="print-btn no-print" onclick="window.print()">🖨️ Salvar como PDF / Imprimir</button>
            </div>
        </div>

        <!-- KPIs Estratégicos -->
        <div class="grid-kpis">
            <div class="kpi-card">
                <div class="kpi-label">MRR em Risco</div>
                <div class="kpi-value" style="color: #dc2626;">R$ {kpis["total_mrr_at_risk"]:,.2f}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">MRR Salvo (Real)</div>
                <div class="kpi-value" style="color: #059669;">R$ {kpis["total_mrr_saved"]:,.2f}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Clientes em Risco Crítico</div>
                <div class="kpi-value" style="color: #d97706;">{kpis["high_risk_customers"]}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Taxa de Sucesso</div>
                <div class="kpi-value" style="color: #4f46e5;">{kpis["retention_success_rate_pct"]}%</div>
            </div>
        </div>

        <!-- Eficácia de Playbooks -->
        <div class="section-title">1. Desempenho e Eficácia dos Playbooks de Retenção</div>
        <table>
            <thead>
                <tr>
                    <th>Playbook Estratégico</th>
                    <th style="text-align: center;">Ações Disparadas</th>
                    <th style="text-align: right;">Economia Anual Projetada</th>
                </tr>
            </thead>
            <tbody>
                {playbooks_rows}
            </tbody>
        </table>

        <!-- Top 10 Clientes em Risco -->
        <div class="section-title">2. Contas Prioritárias em Risco Crítico (Top Drivers SHAP)</div>
        <table>
            <thead>
                <tr>
                    <th>ID Cliente</th>
                    <th style="text-align: center;">Prob. Churn</th>
                    <th style="text-align: right;">MRR em Risco</th>
                    <th>Principais Drivers de Risco</th>
                    <th>Ação Recomendada</th>
                </tr>
            </thead>
            <tbody>
                {accounts_rows}
            </tbody>
        </table>

        <!-- Governança MLOps -->
        <div class="section-title">3. Governança e Saúde do Ecossistema MLOps</div>
        <div class="mlops-box">
            <b>Modelo Champion em Produção:</b> <code>{mlops["active_champion"]}</code> (Catálogo com {mlops["models_in_registry"]} modelos)<br>
            <b>Último Ciclo de Continuous Training (CT):</b> {last_job_html}
        </div>

        <div class="footer">
            <span>RetainIQ • Documento Executivo de Alta Confidencialidade • Gerado Automaticamente</span>
            <span>Página 1 de 1</span>
        </div>
    </div>
</body>
</html>
"""


executive_reporter = ExecutiveReportGenerator()
