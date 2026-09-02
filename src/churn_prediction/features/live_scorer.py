import datetime

from pydantic import BaseModel, Field

from churn_prediction.features.store import feature_store
from churn_prediction.streaming.broadcaster import LiveEventMessage, sse_broadcaster


class LiveCustomerScoreUpdate(BaseModel):
    """Atualização dinâmica de probabilidade de churn de um cliente em tempo real."""

    customer_id: str
    tenant_id: str = "tenant-default"
    previous_risk_score: float
    new_risk_score: float
    risk_delta: float
    risk_level: str  # Baixo | Médio | Alto | Crítico
    reasons: list[str] = Field(default_factory=list)
    recommended_action: str = "Monitoramento Contínuo"
    updated_at: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())


class LiveScorerEngine:
    """Motor de reavaliação de churn dinâmico alimentado pela Feature Store Online."""

    def __init__(self):
        self._customer_scores: dict[str, LiveCustomerScoreUpdate] = {}
        self._init_mock_baselines()

    def _init_mock_baselines(self) -> None:
        """Inicializa baselines para clientes padrão."""
        sample_ids = [
            ("7590-VHVEG", "tenant-tim", 0.18),
            ("5575-GNVDE", "tenant-vivo", 0.22),
            ("3668-QPYBK", "tenant-claro", 0.35),
            ("9237-HQITU", "tenant-vivo", 0.42),
            ("9305-CDSKC", "tenant-tim", 0.28),
        ]
        for cid, tid, base in sample_ids:
            self._customer_scores[cid] = LiveCustomerScoreUpdate(
                customer_id=cid,
                tenant_id=tid,
                previous_risk_score=base,
                new_risk_score=base,
                risk_delta=0.0,
                risk_level="Baixo" if base < 0.30 else "Médio",
                reasons=["Baseline inicial de contrato"],
                recommended_action="Manter plano atual",
            )

    def re_score_customer(
        self, customer_id: str, tenant_id: str = "tenant-default"
    ) -> LiveCustomerScoreUpdate:
        """Recalcula a probabilidade de churn do cliente a partir da telemetria viva da Feature Store."""
        # Busca features online combinadas (Batch + Stream Windows)
        features_list = feature_store.get_online_features(customer_ids=[customer_id])
        feats = features_list[0] if features_list else {}

        # Recupera score anterior
        prev_update = self._customer_scores.get(customer_id)
        prev_score = prev_update.new_risk_score if prev_update else 0.20

        # Fatores da janela de streaming em tempo real
        latency_15m = float(feats.get("avg_latency_15min", 25.0))
        packet_loss_15m = float(feats.get("avg_packet_loss_15min", 0.2))
        disconnects_1h = int(feats.get("disconnect_count_1h", 0))
        failed_payments = int(feats.get("failed_payment_count_24h", 0))
        crm_sentiment = float(feats.get("avg_sentiment_7d", 0.2))
        instability_score = float(feats.get("realtime_instability_score", 0.0))

        # Cálculo do novo score de risco de churn
        # Baseline estrutural (~0.20 a 0.40) + impacto da telemetria viva
        telemetry_impact = (
            (instability_score * 0.45)
            + (min(disconnects_1h, 5) * 0.08)
            + (min(failed_payments, 3) * 0.12)
            + (max(0.0, -crm_sentiment) * 0.15)
        )
        new_score = round(min(0.98, max(0.05, prev_score * 0.5 + telemetry_impact + 0.10)), 3)
        delta = round(new_score - prev_score, 3)

        # Classificação de Risco
        if new_score >= 0.70:
            level = "Crítico"
        elif new_score >= 0.50:
            level = "Alto"
        elif new_score >= 0.30:
            level = "Médio"
        else:
            level = "Baixo"

        # Diagnóstico de motivos
        reasons = []
        if disconnects_1h >= 2:
            reasons.append(f"{disconnects_1h} quedas de conexão na última hora")
        if latency_15m > 80.0 or packet_loss_15m > 3.0:
            reasons.append(
                f"Degradação de rede (latência {latency_15m:.0f}ms, perda {packet_loss_15m:.1f}%)"
            )
        if failed_payments > 0:
            reasons.append(f"{failed_payments} falha(s) de pagamento na fatura")
        if crm_sentiment < -0.3:
            reasons.append("Sentimento negativo em interações recentes de suporte")
        if not reasons:
            reasons.append("Telemetria e pagamentos operando dentro dos parâmetros normais")

        # Recomendação de Playbook
        if "quedas" in " ".join(reasons) or "Degradação" in " ".join(reasons):
            action = "Oferecer suporte técnico prioritário com visita técnica gratuita"
        elif failed_payments > 0:
            action = "Reenviar link de PIX sem juros ou parcelar fatura"
        elif new_score >= 0.60:
            action = "Aplicar desconto preventivo de 20% com migração para plano fidelizado"
        else:
            action = "Manter acompanhamento de rotina"

        update = LiveCustomerScoreUpdate(
            customer_id=customer_id,
            tenant_id=tenant_id,
            previous_risk_score=prev_score,
            new_risk_score=new_score,
            risk_delta=delta,
            risk_level=level,
            reasons=reasons,
            recommended_action=action,
        )
        self._customer_scores[customer_id] = update

        # Emite evento de reavaliação no SSE Broadcaster
        sse_broadcaster.publish(
            LiveEventMessage(
                event_type="RE_SCORE",
                tenant_id=tenant_id,
                customer_id=customer_id,
                data=update.model_dump(),
            )
        )

        return update

    def get_top_live_risk_customers(
        self, tenant_id: str = "tenant-default", limit: int = 20
    ) -> list[LiveCustomerScoreUpdate]:
        """Retorna os clientes com maior risco dinâmico atualizado."""
        filtered = [
            u
            for u in self._customer_scores.values()
            if tenant_id == "tenant-default" or u.tenant_id == tenant_id
        ]
        return sorted(filtered, key=lambda x: x.new_risk_score, reverse=True)[:limit]


# Instância Singleton do Live Scorer
live_scorer = LiveScorerEngine()
