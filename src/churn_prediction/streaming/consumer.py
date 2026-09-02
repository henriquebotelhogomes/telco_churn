import asyncio
import json
import logging
from typing import Any

from churn_prediction.streaming.window_processor import window_processor

logger = logging.getLogger(__name__)


class StreamingKafkaConsumerWorker:
    """Worker assíncrono que consome dos tópicos Kafka/Redpanda e alimenta o processador de janelas."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:19092",
        group_id: str = "retainiq-stream-window-processor",
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = [
            "telemetry.network.events",
            "billing.payment.events",
            "crm.interaction.events",
        ]
        self._consumer: Any = None
        self._running: bool = False
        self._task: asyncio.Task[None] | None = None

    async def _consume_loop(self) -> None:
        """Loop contínuo de consumo de mensagens do Kafka."""
        try:
            from aiokafka import AIOKafkaConsumer

            self._consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset="latest",
                enable_auto_commit=True,
                request_timeout_ms=3000,
            )
            await self._consumer.start()
            logger.info(
                f"[STREAMING CONSUMER] Conectado e escutando tópicos {self.topics} em {self.bootstrap_servers}"
            )

            while self._running:
                try:
                    # Timeout curto para permitir cancelamento limpo
                    msg_batch = await self._consumer.getmany(timeout_ms=1000, max_records=50)
                    for _, messages in msg_batch.items():
                        for msg in messages:
                            try:
                                payload = json.loads(msg.value.decode("utf-8"))
                                alert = window_processor.process_event(payload)

                                customer_id = payload.get("customer_id")
                                tenant_id = payload.get("tenant_id", "tenant-default")

                                # 1. Re-avalia o risco em tempo real
                                if customer_id:
                                    from churn_prediction.features.live_scorer import live_scorer

                                    live_scorer.re_score_customer(customer_id, tenant_id)

                                # 2. Transmite o evento bruto para o SSE
                                from churn_prediction.streaming.broadcaster import (
                                    LiveEventMessage,
                                    sse_broadcaster,
                                )

                                sse_broadcaster.publish(
                                    LiveEventMessage(
                                        event_type=payload.get("event_type", "TELEMETRY"),
                                        tenant_id=tenant_id,
                                        customer_id=customer_id,
                                        data=payload,
                                    )
                                )

                                # 3. Se um alerta reativo foi disparado, transmite imediatamente
                                if alert:
                                    sse_broadcaster.publish(
                                        LiveEventMessage(
                                            event_type="ALERT",
                                            tenant_id=alert.tenant_id,
                                            customer_id=alert.customer_id,
                                            data=alert.model_dump(),
                                        )
                                    )
                            except Exception as e:
                                logger.debug(f"[STREAMING CONSUMER] Erro ao processar evento: {e}")
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.debug(f"[STREAMING CONSUMER] Erro no loop de consumo: {e}")
                    await asyncio.sleep(2)
        except Exception as e:
            logger.info(
                f"[STREAMING CONSUMER] Kafka não acessível em {self.bootstrap_servers} ({e}). Operando via feed local."
            )
        finally:
            if self._consumer is not None:
                try:
                    await self._consumer.stop()
                except Exception:
                    pass
                self._consumer = None

    def start(self) -> None:
        """Inicia o worker de consumo em background."""
        if not self._running:
            self._running = True
            try:
                loop = asyncio.get_running_loop()
                self._task = loop.create_task(self._consume_loop())
            except RuntimeError:
                pass

    def stop(self) -> None:
        """Pausa o worker de consumo."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()


# Instância Singleton do Consumidor
consumer_worker = StreamingKafkaConsumerWorker()
