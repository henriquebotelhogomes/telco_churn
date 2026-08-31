import json
import logging
from typing import Any

from churn_prediction.streaming.generator import generator_instance
from churn_prediction.streaming.schemas import AnyStreamingEvent

logger = logging.getLogger(__name__)


class StreamingProducerRouter:
    """Roteador de publicação de eventos com suporte a Kafka e fallback in-memory."""

    def __init__(self, bootstrap_servers: str = "localhost:19092"):
        self.bootstrap_servers = bootstrap_servers
        self.kafka_available: bool = False
        self._producer: Any = None

    async def publish_event(self, event: AnyStreamingEvent) -> bool:
        """Publica o evento no Kafka se disponível, ou no buffer do gerador."""
        event_dict = event.model_dump()
        topic = event.topic

        if self.kafka_available and self._producer is not None:
            try:
                # Serialização em JSON para o Kafka
                payload = json.dumps(event_dict).encode("utf-8")
                key = event.customer_id.encode("utf-8")
                await self._producer.send_and_wait(topic, key=key, value=payload)
                return True
            except Exception as e:
                logger.warning(f"Falha ao publicar no Kafka ({topic}): {e}. Usando buffer local.")

        # Fallback local
        generator_instance.recent_events.append(event_dict)
        generator_instance.total_generated[topic] = (
            generator_instance.total_generated.get(topic, 0) + 1
        )
        return True


# Instância Singleton do Roteador
producer_router = StreamingProducerRouter()
