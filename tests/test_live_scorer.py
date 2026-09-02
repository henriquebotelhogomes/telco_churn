from churn_prediction.features.live_scorer import LiveScorerEngine
from churn_prediction.streaming.window_processor import window_processor


def test_live_scorer_initial_baselines():
    engine = LiveScorerEngine()
    top_customers = engine.get_top_live_risk_customers(limit=10)
    assert len(top_customers) > 0
    assert all(0.0 <= c.new_risk_score <= 1.0 for c in top_customers)


def test_live_scorer_risk_level_classification():
    engine = LiveScorerEngine()
    cid = "TEST-CID-001"
    tid = "tenant-vivo"

    # Sem instabilidade
    update = engine.re_score_customer(cid, tid)
    assert update.customer_id == cid
    assert update.tenant_id == tid
    assert update.risk_level in ["Baixo", "Médio", "Alto", "Crítico"]


def test_live_scorer_reasons_and_recommended_action_on_instability():
    engine = LiveScorerEngine()
    cid = "TEST-CID-002"
    tid = "tenant-claro"

    # Injeta evento de instabilidade de rede no window_processor
    for _ in range(3):
        window_processor.process_event(
            {
                "event_type": "FIBER_DISCONNECT",
                "topic": "telemetry.network.events",
                "tenant_id": tid,
                "customer_id": cid,
                "latency_ms": 220.0,
                "packet_loss_pct": 18.0,
                "disconnect_count_last_hour": 4,
            }
        )

    update = engine.re_score_customer(cid, tid)
    assert update.new_risk_score > 0.30
    assert any("quedas" in r.lower() or "degradação" in r.lower() for r in update.reasons)
    assert "suporte técnico prioritário" in update.recommended_action.lower()


def test_live_scorer_multitenant_filtering():
    engine = LiveScorerEngine()
    engine.re_score_customer("CUST-VIVO-1", tenant_id="tenant-vivo")
    engine.re_score_customer("CUST-TIM-1", tenant_id="tenant-tim")

    vivo_top = engine.get_top_live_risk_customers(tenant_id="tenant-vivo")
    assert all(c.tenant_id == "tenant-vivo" for c in vivo_top)

    tim_top = engine.get_top_live_risk_customers(tenant_id="tenant-tim")
    assert all(c.tenant_id == "tenant-tim" for c in tim_top)
