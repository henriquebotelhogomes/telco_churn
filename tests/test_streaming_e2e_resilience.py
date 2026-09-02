import time

from churn_prediction.streaming.broadcaster import LiveEventMessage, SSEBroadcaster
from churn_prediction.streaming.schemas import NetworkEventType, NetworkTelemetryEvent


def test_streaming_e2e_latency_and_resilience():
    """Valida SLA de latência end-to-end (< 50ms) e resiliência em 500 mensagens consecutivas."""
    broadcaster = SSEBroadcaster()
    queue = broadcaster.subscribe("tenant-perf-test")
    latencies = []

    try:
        # Envia 500 mensagens consecutivas medindo tempo de difusão
        for i in range(500):
            t_start = time.perf_counter()

            evt = NetworkTelemetryEvent(
                event_id=f"perf_evt_{i}",
                customer_id=f"CLI-PERF-{i % 50}",
                tenant_id="tenant-perf-test",
                event_type=NetworkEventType.HEARTBEAT,
                download_speed_mbps=100.0,
                upload_speed_mbps=50.0,
                latency_ms=15.0,
                packet_loss_pct=0.0,
            )

            msg = LiveEventMessage(
                event_type="TELEMETRY",
                tenant_id=evt.tenant_id,
                customer_id=evt.customer_id,
                data=evt.model_dump(),
            )
            broadcaster.publish(msg)

            # Consome da fila
            received = queue.get_nowait()
            t_end = time.perf_counter()

            latency_ms = (t_end - t_start) * 1000.0
            latencies.append(latency_ms)
            assert received.customer_id == evt.customer_id

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        # Critérios de Aceite do PRD: Latência < 50ms
        assert avg_latency < 10.0, f"Latência média {avg_latency:.2f}ms excedeu meta de 10ms"
        assert p95_latency < 50.0, f"P95 de latência {p95_latency:.2f}ms excedeu meta de 50ms"
        assert len(latencies) == 500

    finally:
        broadcaster.unsubscribe(queue, "tenant-perf-test")
