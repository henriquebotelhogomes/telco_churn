import asyncio
import logging
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

STREAMING_TOPICS = [
    "telemetry.network.events",
    "billing.payment.events",
    "crm.interaction.events",
]


async def provision_topics(bootstrap_servers: str = "localhost:19092") -> bool:
    """Cria e valida tópicos no broker Redpanda/Kafka."""
    try:
        from aiokafka.admin import AIOKafkaAdminClient, NewTopic
    except ImportError:
        logger.error("[PROVISION] 'aiokafka' não está instalado no ambiente.")
        return False

    logger.info(f"[PROVISION] Conectando ao broker em {bootstrap_servers}...")
    admin = AIOKafkaAdminClient(bootstrap_servers=bootstrap_servers, request_timeout_ms=5000)

    try:
        await admin.start()
        existing_topics = await admin.list_topics()
        logger.info(f"[PROVISION] Tópicos existentes no broker: {existing_topics}")

        new_topics = []
        for topic_name in STREAMING_TOPICS:
            if topic_name not in existing_topics:
                new_topics.append(
                    NewTopic(
                        name=topic_name,
                        num_partitions=1,
                        replication_factor=1,
                    )
                )
                logger.info(f"[PROVISION] Tópico agendado para criação: {topic_name}")
            else:
                logger.info(f"[PROVISION] Tópico '{topic_name}' já existe. Ignorando criação.")

        if new_topics:
            await admin.create_topics(new_topics)
            logger.info(f"[PROVISION] Sucesso: {len(new_topics)} novos tópicos criados!")
        else:
            logger.info(
                "[PROVISION] Todos os tópicos já estão provisionados e prontos para streaming."
            )

        return True
    except Exception as e:
        logger.warning(
            f"[PROVISION] Não foi possível conectar ao Redpanda/Kafka em {bootstrap_servers}: {e}"
        )
        logger.info(
            "[PROVISION] Certifique-se de executar 'docker compose -f docker-compose.streaming.yml up -d'."
        )
        return False
    finally:
        await admin.close()


if __name__ == "__main__":
    servers = sys.argv[1] if len(sys.argv) > 1 else "localhost:19092"
    success = asyncio.run(provision_topics(servers))
    sys.exit(0 if success else 1)
