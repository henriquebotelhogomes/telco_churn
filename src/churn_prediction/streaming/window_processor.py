import datetime
import uuid
from collections import defaultdict, deque
from typing import Any

from pydantic import BaseModel, Field


class RealtimeRiskAlert(BaseModel):
    """Alerta de risco emitido em tempo real pelo motor de streaming."""
    alert_id: str = Field(..., description="ID único do alerta")
    customer_id: str = Field(..., description="ID do cliente")
    severity: str = Field(..., description="CRITICA | ALTA | MEDIA")
    trigger_reason: str = Field(..., description="Condição de streaming que disparou o alerta")
    recommended_intervention: str = Field(..., description="Ação comercial/técnica imediata sugerida")
    instability_score: float = Field(..., ge=0.0, le=1.0, description="Score instantâneo de instabilidade")
    created_at: str = Field(..., description="Timestamp ISO do disparo")
    acknowledged: bool = Field(default=False, description="Se o alerta já foi tratado")
    acknowledged_by: str | None = Field(default=None, description="Operador que tratou o alerta")


class CustomerWindowMetrics(BaseModel):
    """Métricas agregadas em janelas deslizantes para um cliente."""
    customer_id: str
    tenant_id: str = "tenant-default"
    avg_latency_15min: float = Field(default=0.0, description="Latência média dos últimos 15 min (ms)")
    avg_packet_loss_15min: float = Field(default=0.0, description="Perda média de pacotes nos últimos 15 min (%)")
    disconnect_count_1h: int = Field(default=0, description="Total de quedas de conexão na última hora")
    failed_payment_count_24h: int = Field(default=0, description="Tentativas de pagamento falhas nas últimas 24h")
    negative_crm_count_7d: int = Field(default=0, description="Interações de CRM negativas (sentimento <= -0.5) nos últimos 7 dias")
    avg_sentiment_7d: float = Field(default=0.0, description="Sentimento médio dos contatos nos últimos 7 dias")
    realtime_instability_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Índice de risco/instabilidade em tempo real")
    last_event_timestamp: str = Field(default="", description="Data/hora do último evento processado")
    total_events_processed: int = Field(default=0, description="Total de eventos acumulados na história recente")


class StreamWindowProcessor:
    """Motor de processamento de fluxo contínuo com janelas deslizantes e disparo de alertas."""

    def __init__(self, max_alerts_history: int = 200):
        # Armazena eventos recentes particionados por cliente e por tipo
        # Cada item: (timestamp_epoch_seconds, payload_dict)
        self._network_events: dict[str, deque[tuple[float, dict[str, Any]]]] = defaultdict(deque)
        self._billing_events: dict[str, deque[tuple[float, dict[str, Any]]]] = defaultdict(deque)
        self._crm_events: dict[str, deque[tuple[float, dict[str, Any]]]] = defaultdict(deque)

        # Cache de métricas calculadas por cliente
        self._metrics_cache: dict[str, CustomerWindowMetrics] = {}
        # Fila de alertas emitidos
        self._alerts: deque[RealtimeRiskAlert] = deque(maxlen=max_alerts_history)
        # Controle de deduplicação de alertas recentes por cliente (evita spam de alertas)
        self._last_alert_time: dict[str, float] = {}

    def _parse_timestamp(self, ts_str: str | None) -> float:
        """Converte ISO timestamp para epoch timestamp em segundos."""
        if not ts_str:
            return datetime.datetime.now(datetime.UTC).timestamp()
        try:
            dt = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            return dt.timestamp()
        except Exception:
            return datetime.datetime.now(datetime.UTC).timestamp()

    def _evict_stale_events(self, customer_id: str, current_time: float) -> None:
        """Descarta eventos fora das janelas máximas (15 min, 1h, 24h, 7d)."""
        # 1. Rede: Janela máxima de 1 hora (3600s)
        cutoff_net = current_time - 3600.0
        net_deque = self._network_events[customer_id]
        while net_deque and net_deque[0][0] < cutoff_net:
            net_deque.popleft()

        # 2. Billing: Janela de 24 horas (86400s)
        cutoff_bill = current_time - 86400.0
        bill_deque = self._billing_events[customer_id]
        while bill_deque and bill_deque[0][0] < cutoff_bill:
            bill_deque.popleft()

        # 3. CRM: Janela de 7 dias (604800s)
        cutoff_crm = current_time - 604800.0
        crm_deque = self._crm_events[customer_id]
        while crm_deque and crm_deque[0][0] < cutoff_crm:
            crm_deque.popleft()

    def process_event(self, event_data: dict[str, Any]) -> RealtimeRiskAlert | None:
        """Ingere e processa um evento em tempo real, atualizando janelas e verificando alertas."""
        customer_id = str(event_data.get("customer_id") or "UNKNOWN")
        tenant_id = str(event_data.get("tenant_id") or "tenant-default")
        topic = str(event_data.get("topic") or "")
        ts_str = str(event_data.get("timestamp") or datetime.datetime.now(datetime.UTC).isoformat())
        ts_epoch = self._parse_timestamp(ts_str)

        # 1. Roteamento do evento para a janela correspondente
        if "telemetry" in topic or "download_speed_mbps" in event_data:
            self._network_events[customer_id].append((ts_epoch, event_data))
        elif "billing" in topic or "invoice_amount" in event_data:
            self._billing_events[customer_id].append((ts_epoch, event_data))
        elif "crm" in topic or "sentiment_score" in event_data:
            self._crm_events[customer_id].append((ts_epoch, event_data))

        # 2. Limpeza de eventos antigos (Eviction)
        self._evict_stale_events(customer_id, ts_epoch)

        # 3. Cálculo das Janelas Deslizantes
        metrics = self._calculate_windows(customer_id, tenant_id, ts_epoch, ts_str)
        self._metrics_cache[customer_id] = metrics

        # 4. Avaliação de Regras de Alerta Reativo Imediato
        alert = self._evaluate_alerts(customer_id, metrics, ts_epoch, ts_str)
        if alert is not None:
            self._alerts.append(alert)
        return alert

    def _calculate_windows(
        self, customer_id: str, tenant_id: str, current_time: float, last_ts_str: str
    ) -> CustomerWindowMetrics:
        """Calcula as agregações nas janelas deslizantes para o cliente."""
        # Janela 15 Minutos (Rede)
        cutoff_15m = current_time - 900.0
        net_15m = [e for ts, e in self._network_events[customer_id] if ts >= cutoff_15m]
        latencies_15m = [float(e.get("latency_ms", 0.0)) for e in net_15m]
        packets_15m = [float(e.get("packet_loss_pct", 0.0)) for e in net_15m]

        avg_latency = round(sum(latencies_15m) / len(latencies_15m), 1) if latencies_15m else 0.0
        avg_packet_loss = round(sum(packets_15m) / len(packets_15m), 1) if packets_15m else 0.0

        # Janela 1 Hora (Rede - Quedas acumuladas)
        disconnects_1h = sum(
            int(e.get("disconnect_count_last_hour", 0))
            if e.get("event_type") == "FIBER_DISCONNECT" or int(e.get("disconnect_count_last_hour", 0)) > 0
            else 0
            for _, e in self._network_events[customer_id]
        )

        # Janela 24 Horas (Billing - Falhas de pagamento)
        failed_payments_24h = sum(
            1 for _, e in self._billing_events[customer_id]
            if str(e.get("event_type")) == "PAYMENT_FAILED" or e.get("error_code") is not None
        )

        # Janela 7 Dias (CRM - Sentimento e reclamações)
        crm_events = [e for _, e in self._crm_events[customer_id]]
        sentiments = [float(e.get("sentiment_score", 0.0)) for e in crm_events]
        avg_sentiment = round(sum(sentiments) / len(sentiments), 2) if sentiments else 0.0
        negative_crm_count = sum(1 for s in sentiments if s <= -0.40)

        # Total de eventos processados
        total_evts = (
            len(self._network_events[customer_id])
            + len(self._billing_events[customer_id])
            + len(self._crm_events[customer_id])
        )

        # Score ponderado de instabilidade em tempo real (0.0 a 1.0)
        score_net = min(0.40, (disconnects_1h / 3.0) * 0.40) + min(0.20, (avg_latency / 200.0) * 0.20)
        score_bill = min(0.25, (failed_payments_24h / 2.0) * 0.25)
        score_crm = 0.15 if (negative_crm_count > 0 or avg_sentiment < -0.3) else 0.0

        instability_score = round(min(1.0, score_net + score_bill + score_crm), 2)

        return CustomerWindowMetrics(
            customer_id=customer_id,
            tenant_id=tenant_id,
            avg_latency_15min=avg_latency,
            avg_packet_loss_15min=avg_packet_loss,
            disconnect_count_1h=disconnects_1h,
            failed_payment_count_24h=failed_payments_24h,
            negative_crm_count_7d=negative_crm_count,
            avg_sentiment_7d=avg_sentiment,
            realtime_instability_score=instability_score,
            last_event_timestamp=last_ts_str,
            total_events_processed=total_evts,
        )

    def _evaluate_alerts(
        self,
        customer_id: str,
        metrics: CustomerWindowMetrics,
        current_time: float,
        ts_str: str,
    ) -> RealtimeRiskAlert | None:
        """Verifica se as condições de streaming justificam emissão de alerta imediato."""
        # Throttle: não emite alertas repetidos para o mesmo cliente dentro de 60 segundos
        last_time = self._last_alert_time.get(customer_id, 0.0)
        if (current_time - last_time) < 60.0:
            return None

        # Condição 1: Degradação severa de rede
        if metrics.disconnect_count_1h >= 3 or (metrics.avg_latency_15min >= 150.0 and metrics.avg_packet_loss_15min >= 10.0):
            self._last_alert_time[customer_id] = current_time
            return RealtimeRiskAlert(
                alert_id=f"alt_{uuid.uuid4().hex[:8]}",
                customer_id=customer_id,
                severity="CRITICA",
                trigger_reason=f"Degradação crítica de rede: {metrics.disconnect_count_1h} quedas na última 1h (latência {metrics.avg_latency_15min}ms)",
                recommended_intervention="Abrir ordem técnica prioritária e enviar bonificação preventiva de dados via SMS/WhatsApp.",
                instability_score=metrics.realtime_instability_score,
                created_at=ts_str,
            )

        # Condição 2: Falha financeira combinada com insatisfação
        if metrics.failed_payment_count_24h >= 1 and metrics.negative_crm_count_7d >= 1:
            self._last_alert_time[customer_id] = current_time
            return RealtimeRiskAlert(
                alert_id=f"alt_{uuid.uuid4().hex[:8]}",
                customer_id=customer_id,
                severity="ALTA",
                trigger_reason=f"Risco financeiro com insatisfação: {metrics.failed_payment_count_24h} falhas de cobrança e {metrics.negative_crm_count_7d} reclamações recentes",
                recommended_intervention="Acionar contato ativo de retenção (Playbook AUTOMATIZACAO_PAGAMENTO com desconto emergencial).",
                instability_score=metrics.realtime_instability_score,
                created_at=ts_str,
            )

        # Condição 3: Alto score geral de volatilidade
        if metrics.realtime_instability_score >= 0.70:
            self._last_alert_time[customer_id] = current_time
            return RealtimeRiskAlert(
                alert_id=f"alt_{uuid.uuid4().hex[:8]}",
                customer_id=customer_id,
                severity="ALTA",
                trigger_reason=f"Instabilidade operacional elevada (Score: {metrics.realtime_instability_score:.2f})",
                recommended_intervention="Intervenção proativa no próximo contato e verificação preventiva do pacote de serviços.",
                instability_score=metrics.realtime_instability_score,
                created_at=ts_str,
            )

        return None

    def get_customer_windows(self, customer_id: str) -> CustomerWindowMetrics | None:
        """Retorna o snapshot das janelas deslizantes de um cliente específico."""
        return self._metrics_cache.get(customer_id)

    def get_all_windows(self, limit: int = 50) -> list[CustomerWindowMetrics]:
        """Retorna a lista de clientes ordenados pelos mais instáveis/recentes."""
        sorted_list = sorted(
            self._metrics_cache.values(),
            key=lambda m: (m.realtime_instability_score, m.total_events_processed),
            reverse=True,
        )
        return sorted_list[:limit]

    def get_active_alerts(self, limit: int = 50) -> list[RealtimeRiskAlert]:
        """Retorna a lista dos alertas mais recentes."""
        return list(reversed(self._alerts))[:limit]

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "operator") -> bool:
        """Marca um alerta como tratado."""
        for alt in self._alerts:
            if alt.alert_id == alert_id:
                alt.acknowledged = True
                alt.acknowledged_by = acknowledged_by
                return True
        return False


# Instância Singleton do Processador de Janelas
window_processor = StreamWindowProcessor()
