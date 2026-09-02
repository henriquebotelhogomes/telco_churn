"""Módulo de Engenharia de Dados Sintéticos e Aumento de Dados Corporativo (Telco 360 Enterprise).

Gera bases de dados enriquecidas com causalidade física de redes FTTH/5G, CRM omnichannel,
NPS, sentimentos no WhatsApp e faturamento em conformidade com a LGPD.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def generate_enterprise_dataset(
    num_samples: int = 7043,
    chaos_ratio: float = 0.12,
    seed: int = 42,
) -> pd.DataFrame:
    """Gera um DataFrame com dados enriquecidos de telecomunicações corporativas.

    Preserva as 19 colunas canônicas do contrato EN-US e adiciona 16+ colunas
    avançadas de telemetria de rede (QoE), CRM, NPS e faturamento BRL.
    """
    random.seed(seed)
    np.random.seed(seed)

    ufs = ["SP", "RJ", "MG", "RS", "PR", "BA", "PE", "DF", "SC", "GO"]
    uf_weights = [0.35, 0.15, 0.12, 0.08, 0.07, 0.06, 0.05, 0.05, 0.04, 0.03]
    operators = ["Vivo", "Claro", "TIM"]
    op_weights = [0.38, 0.34, 0.28]

    records: list[dict[str, Any]] = []

    for i in range(1, num_samples + 1):
        operator = random.choices(operators, weights=op_weights)[0]
        prefix = operator.upper()
        cid = f"{prefix}-{i:05d}-{random.randint(100, 999)}"

        gender = random.choice(["Male", "Female"])
        senior = 1 if random.random() < 0.16 else 0
        partner = "Yes" if random.random() < 0.48 else "No"
        dependents = "Yes" if partner == "Yes" and random.random() < 0.55 else "No"

        # Tenure (meses de permanência)
        tenure = int(np.clip(np.random.exponential(scale=28.0), 1, 72))

        # Contrato
        if tenure > 36:
            contract = random.choices(
                ["Month-to-month", "One year", "Two year"], weights=[0.20, 0.35, 0.45]
            )[0]
        elif tenure > 12:
            contract = random.choices(
                ["Month-to-month", "One year", "Two year"], weights=[0.45, 0.40, 0.15]
            )[0]
        else:
            contract = random.choices(
                ["Month-to-month", "One year", "Two year"], weights=[0.75, 0.20, 0.05]
            )[0]

        phone_service = "Yes" if random.random() < 0.90 else "No"
        multiple_lines = (
            "Yes"
            if phone_service == "Yes" and random.random() < 0.42
            else ("No" if phone_service == "Yes" else "No phone service")
        )

        # Tipo de Internet & Plan Speed
        internet = random.choices(["Fiber optic", "DSL", "No"], weights=[0.55, 0.34, 0.11])[0]
        if internet == "Fiber optic":
            plan_speed_mbps = random.choice([300, 500, 700, 1000])
        elif internet == "DSL":
            plan_speed_mbps = random.choice([50, 100])
        else:
            plan_speed_mbps = 0

        # Serviços Adicionais
        if internet != "No":
            sec = "Yes" if random.random() < 0.35 else "No"
            backup = "Yes" if random.random() < 0.40 else "No"
            dev = "Yes" if random.random() < 0.38 else "No"
            tech = "Yes" if random.random() < 0.32 else "No"
            tv = "Yes" if random.random() < 0.45 else "No"
            movies = "Yes" if random.random() < 0.45 else "No"
        else:
            sec = backup = dev = tech = tv = movies = "No internet service"

        paperless = "Yes" if random.random() < 0.60 else "No"
        payment_method = random.choices(
            [
                "Electronic check",
                "Mailed check",
                "Bank transfer (automatic)",
                "Credit card (automatic)",
            ],
            weights=[0.35, 0.15, 0.25, 0.25],
        )[0]

        # Injeção de Caos / Instabilidade de Rede
        is_chaotic = random.random() < chaos_ratio

        if is_chaotic and internet != "No":
            fiber_outages = random.randint(3, 7)
            avg_latency = round(random.uniform(110.0, 320.0), 1)
            packet_loss = round(random.uniform(8.0, 35.0), 2)
            download_speed = round(plan_speed_mbps * random.uniform(0.15, 0.45), 1)
            modem_reboots = random.randint(4, 12)
            tech_visits = random.randint(1, 4)
            nps = random.randint(0, 4)
            csat = round(random.uniform(1.0, 2.5), 1)
            sentiment_whatsapp = round(random.uniform(-0.95, -0.40), 2)
            crm_tickets = random.randint(2, 6)
            anatel_complaint = 1 if random.random() < 0.45 else 0
            billing_disputes = random.randint(1, 3)
        else:
            fiber_outages = random.choices([0, 1, 2], weights=[0.75, 0.20, 0.05])[0]
            avg_latency = round(random.uniform(12.0, 42.0), 1)
            packet_loss = round(random.uniform(0.05, 1.20), 2)
            download_speed = (
                round(plan_speed_mbps * random.uniform(0.85, 1.05), 1)
                if plan_speed_mbps > 0
                else 0.0
            )
            modem_reboots = random.choices([0, 1, 2], weights=[0.60, 0.30, 0.10])[0]
            tech_visits = 0 if random.random() < 0.85 else 1
            nps = random.choices([7, 8, 9, 10, 5, 6], weights=[0.25, 0.30, 0.25, 0.10, 0.05, 0.05])[
                0
            ]
            csat = round(random.uniform(3.8, 5.0), 1)
            sentiment_whatsapp = round(random.uniform(0.20, 0.85), 2)
            crm_tickets = random.choices([0, 1], weights=[0.80, 0.20])[0]
            anatel_complaint = 0
            billing_disputes = 0

        # Cálculo da Mensalidade (Monthly Charges)
        base_charge = 25.0
        if phone_service == "Yes":
            base_charge += 20.0
        if multiple_lines == "Yes":
            base_charge += 15.0
        if internet == "Fiber optic":
            base_charge += 55.0 + (plan_speed_mbps / 50.0)
        elif internet == "DSL":
            base_charge += 35.0
        if sec == "Yes":
            base_charge += 12.0
        if backup == "Yes":
            base_charge += 10.0
        if dev == "Yes":
            base_charge += 10.0
        if tech == "Yes":
            base_charge += 15.0
        if tv == "Yes":
            base_charge += 22.0
        if movies == "Yes":
            base_charge += 22.0

        monthly_charges = round(base_charge + random.uniform(-3.0, 3.0), 2)
        total_charges = round(monthly_charges * tenure * random.uniform(0.95, 1.02), 2)

        # Causalidade de Churn Realista
        churn_prob = 0.10
        if contract == "Month-to-month":
            churn_prob += 0.25
        if is_chaotic:
            churn_prob += 0.40
        if payment_method == "Electronic check":
            churn_prob += 0.10
        if tech == "No" and internet != "No":
            churn_prob += 0.08
        if fiber_outages >= 3:
            churn_prob += 0.35
        if anatel_complaint == 1:
            churn_prob += 0.30
        if nps >= 9:
            churn_prob -= 0.25
        if tenure > 24:
            churn_prob -= 0.15

        churn_prob = float(np.clip(churn_prob, 0.02, 0.96))
        churn = "Yes" if random.random() < churn_prob else "No"

        records.append(
            {
                # --- 19 Colunas Canônicas (Compatibilidade Pandera / ML) ---
                "customerID": cid,
                "gender": gender,
                "SeniorCitizen": senior,
                "Partner": partner,
                "Dependents": dependents,
                "tenure": tenure,
                "PhoneService": phone_service,
                "MultipleLines": multiple_lines,
                "InternetService": internet,
                "OnlineSecurity": sec,
                "OnlineBackup": backup,
                "DeviceProtection": dev,
                "TechSupport": tech,
                "StreamingTV": tv,
                "StreamingMovies": movies,
                "Contract": contract,
                "PaperlessBilling": paperless,
                "PaymentMethod": payment_method,
                "MonthlyCharges": monthly_charges,
                "TotalCharges": str(total_charges),
                "Churn": churn,
                # --- 16+ Colunas Enriquecidas Telco 360 Enterprise ---
                "operator": operator,
                "region_uf": random.choices(ufs, weights=uf_weights)[0],
                "plan_speed_mbps": plan_speed_mbps,
                "avg_download_speed_mbps": download_speed,
                "avg_latency_ms": avg_latency,
                "packet_loss_pct_30d": packet_loss,
                "fiber_outages_count_90d": fiber_outages,
                "modem_reboots_count_30d": modem_reboots,
                "technical_visit_count_12m": tech_visits,
                "nps_score": nps,
                "csat_score": csat,
                "whatsapp_sentiment_score": sentiment_whatsapp,
                "crm_tickets_opened_60d": crm_tickets,
                "anatel_complaint_flag": anatel_complaint,
                "billing_disputes_count_12m": billing_disputes,
                "auto_debit_failures_count": random.randint(1, 3) if is_chaotic else 0,
                "price_increase_pct_last_cycle": round(random.uniform(0.0, 15.0), 1),
                "pix_payment_enabled": 1 if random.random() < 0.70 else 0,
                "b2b_cnpj_flag": 1 if monthly_charges > 250.0 and random.random() < 0.35 else 0,
            }
        )

    df = pd.DataFrame(records)
    return df


def main() -> None:
    """CLI para geração do dataset sintético corporativo."""
    parser = argparse.ArgumentParser(
        description="Gerador de Dataset Sintético Telco 360 Enterprise"
    )
    parser.add_argument("--num-samples", type=int, default=7043, help="Número de clientes a gerar")
    parser.add_argument(
        "--chaos-ratio",
        type=float,
        default=0.12,
        help="Proporção de clientes com instabilidade de rede",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/telco_enterprise_customers.csv",
        help="Caminho de saída",
    )
    args = parser.parse_args()

    df = generate_enterprise_dataset(num_samples=args.num_samples, chaos_ratio=args.chaos_ratio)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(
        f"[SUCCESS] Base Telco 360 Enterprise gerada: {out_path} ({len(df)} clientes, {len(df.columns)} colunas)"
    )


if __name__ == "__main__":
    main()
