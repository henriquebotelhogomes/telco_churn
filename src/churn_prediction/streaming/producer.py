import json
import logging
from typing import Any

from churn_prediction.streaming.generator import generator_instance
from churn_prediction.streaming.schemas import AnyStreamingEvent

logger = logging.getLogger(__name__)


class StreamingProducerRouter:
    """Roteador de publicação de eventos com suporte a Kafka/Redpanda e fallback in-memory."""

    def __init__(self, bootstrap_servers: str = "localhost:19092"):
        self.bootstrap_servers = bootstrap_servers
        self._producer: Any = None
        self._initialized: bool = False

    async def _get_producer(self) -> Any:
        if not self._initialized:
            try:
                from aiokafka import AIOKafkaProducer

                producer = AIOKafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    request_timeout_ms=2000,
                    connections_max_idle_ms=10000,
                )
                await producer.start()
                self._producer = producer
                self._initialized = True
                logger.info(
                    f"[STREAMING] Conectado ao Redpanda/Kafka em {self.bootstrap_servers}"
                )
            except Exception as e:
                logger.info(
                    f"[STREAMING] Kafka em {self.bootstrap_servers} indisponível ({e}). Usando buffer in-memory."
                )
                self._producer = None
                self._initialized = True
        return self._producer

    async def publish_event(self, event: AnyStreamingEvent) -> bool:
        """Publica o evento no Kafka se disponível, e sempre atualiza o buffer local."""
        event_dict = event.model_dump()
        topic = event.topic

        # Atualiza buffer e estatísticas do gerador
        generator_instance.recent_events.append(event_dict)
        generator_instance.total_generated[topic] = (
            generator_instance.total_generated.get(topic, 0) + 1
        )

        # Atualiza o processador de janelas em tempo real
        try:
            from churn_prediction.streaming.window_processor import window_processor

            window_processor.process_event(event_dict)
        except Exception as e:
            logger.debug(f"[STREAMING] Erro ao alimentar window_processor: {e}")

        # Tenta enviar para o Kafka/Redpanda
        producer = await self._get_producer()
        if producer is not None:
            try:
                payload = json.dumps(event_dict).encode("utf-8")
                key = event.customer_id.encode("utf-8")
                await producer.send(topic, key=key, value=payload)
            except Exception as e:
                logger.debug(f"[STREAMING] Falha ao enviar para o tópico {topic}: {e}")

        return True

    async def close(self) -> None:
        if self._producer is not None:
            try:
                await self._producer.stop()
            except Exception:
                pass
            self._producer = None
            self._initialized = False


# Instância Singleton do Roteador
producer_router = StreamingProducerRouter()
