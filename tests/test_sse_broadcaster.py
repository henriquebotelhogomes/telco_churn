import asyncio

import pytest

from churn_prediction.streaming.broadcaster import LiveEventMessage, SSEBroadcaster


def test_broadcaster_subscribe_and_unsubscribe():
    broadcaster = SSEBroadcaster()
    queue = broadcaster.subscribe("tenant-alpha")
    assert (queue, "tenant-alpha") in broadcaster._subscribers

    broadcaster.unsubscribe(queue, "tenant-alpha")
    assert (queue, "tenant-alpha") not in broadcaster._subscribers


def test_broadcaster_publish_tenant_isolation():
    broadcaster = SSEBroadcaster()
    queue_alpha = broadcaster.subscribe("tenant-alpha")
    queue_beta = broadcaster.subscribe("tenant-beta")
    queue_global = broadcaster.subscribe("tenant-default")

    try:
        # Mensagem direcionada exclusivamente ao tenant-alpha
        msg_alpha = LiveEventMessage(
            event_type="ALERT",
            tenant_id="tenant-alpha",
            customer_id="CUST-001",
            data={"reason": "fiber_cut"},
        )
        broadcaster.publish(msg_alpha)

        assert not queue_alpha.empty()
        assert not queue_global.empty()
        assert queue_beta.empty()

        received_alpha = queue_alpha.get_nowait()
        assert received_alpha.tenant_id == "tenant-alpha"

        received_global = queue_global.get_nowait()
        assert received_global.tenant_id == "tenant-alpha"

    finally:
        broadcaster.unsubscribe(queue_alpha, "tenant-alpha")
        broadcaster.unsubscribe(queue_beta, "tenant-beta")
        broadcaster.unsubscribe(queue_global, "tenant-default")


def test_broadcaster_queue_overflow_handling():
    broadcaster = SSEBroadcaster()
    queue = broadcaster.subscribe("tenant-test")

    try:
        # Preenche a fila acima do maxsize (100)
        for i in range(110):
            broadcaster.publish(
                LiveEventMessage(
                    event_type="TELEMETRY",
                    tenant_id="tenant-test",
                    customer_id=f"CUST-{i}",
                    data={"idx": i},
                )
            )

        # Não deve travar nem estourar exceção, mantendo o tamanho no limite máximo
        assert queue.qsize() <= 100
    finally:
        broadcaster.unsubscribe(queue, "tenant-test")


def test_broadcaster_event_generator():
    async def _run():
        broadcaster = SSEBroadcaster()

        class MockRequest:
            def __init__(self):
                self.disconnected = False

            async def is_disconnected(self):
                return self.disconnected

        req = MockRequest()
        gen = broadcaster.event_generator(req, tenant_id="tenant-gen")

        # Primeiro evento é sempre o heartbeat de conexão estabelecida
        first_chunk = await anext(gen)
        assert "data:" in first_chunk
        assert "CONNECTED" in first_chunk

        # Encerra gerador
        req.disconnected = True
        with pytest.raises(StopAsyncIteration):
            await anext(gen)

    asyncio.run(_run())
