import asyncio
import datetime
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import Request
from pydantic import BaseModel, Field


class LiveEventMessage(BaseModel):
    """Mensagem de evento transmitida em tempo real via Server-Sent Events (SSE)."""

    event_type: str = Field(
        ..., description="TELEMETRY | PAYMENT | CRM | RE_SCORE | ALERT | HEARTBEAT"
    )
    tenant_id: str = Field(
        default="tenant-default", description="Identificador do tenant/operadora"
    )
    customer_id: str | None = Field(default=None, description="Identificador do cliente afetado")
    data: dict[str, Any] = Field(default_factory=dict, description="Payload de métricas e estado")
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat())


class SSEBroadcaster:
    """Hub central assíncrono para difusão de eventos em tempo real via SSE."""

    def __init__(self):
        self._subscribers: set[tuple[asyncio.Queue[LiveEventMessage], str]] = set()

    def subscribe(self, tenant_id: str = "tenant-default") -> asyncio.Queue[LiveEventMessage]:
        """Inscreve um cliente SSE para receber eventos filtrados pelo tenant."""
        queue: asyncio.Queue[LiveEventMessage] = asyncio.Queue(maxsize=100)
        self._subscribers.add((queue, tenant_id))
        return queue

    def unsubscribe(
        self, queue: asyncio.Queue[LiveEventMessage], tenant_id: str = "tenant-default"
    ) -> None:
        """Remove a inscrição do cliente SSE."""
        self._subscribers.discard((queue, tenant_id))

    def publish(self, message: LiveEventMessage) -> None:
        """Publica um evento para todos os clientes conectados respeitando o tenant."""
        for queue, sub_tenant in list(self._subscribers):
            # Se for tenant-default (Global) ou se o tenant do assinante corresponder ao evento
            if (
                sub_tenant == "tenant-default"
                or sub_tenant == message.tenant_id
                or message.tenant_id == "tenant-default"
            ):
                try:
                    queue.put_nowait(message)
                except asyncio.QueueFull:
                    # Se a fila estiver cheia, descarta a mensagem mais antiga para não bloquear
                    try:
                        queue.get_nowait()
                        queue.put_nowait(message)
                    except Exception:
                        pass

    async def event_generator(
        self, request: Request, tenant_id: str = "tenant-default"
    ) -> AsyncGenerator[str, None]:
        """Gera o stream contínuo de Server-Sent Events (SSE) formatado em text/event-stream."""
        queue = self.subscribe(tenant_id)
        try:
            # Mensagem inicial de conexão estabelecida
            init_msg = LiveEventMessage(
                event_type="HEARTBEAT",
                tenant_id=tenant_id,
                data={"status": "CONNECTED", "subscribed_tenant": tenant_id},
            )
            yield f"data: {init_msg.model_dump_json()}\n\n"

            while True:
                # Se o cliente desconectar a aba/navegador, encerra o generator
                if await request.is_disconnected():
                    break

                try:
                    # Aguarda até 10 segundos por um novo evento ou envia heartbeat
                    message = await asyncio.wait_for(queue.get(), timeout=10.0)
                    yield f"data: {message.model_dump_json()}\n\n"
                except TimeoutError:
                    # Heartbeat periódico para manter o socket HTTP/2 / SSE vivo
                    heartbeat = LiveEventMessage(
                        event_type="HEARTBEAT",
                        tenant_id=tenant_id,
                        data={"ping": "pong"},
                    )
                    yield f"data: {heartbeat.model_dump_json()}\n\n"
        finally:
            self.unsubscribe(queue, tenant_id)


# Instância Singleton do Broadcaster SSE
sse_broadcaster = SSEBroadcaster()
