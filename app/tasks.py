import asyncio
import logging
from taskiq_redis import RedisStreamBroker
from app.core.config import settings

message_broker = RedisStreamBroker(settings.REDIS_URL)

logger = logging.getLogger("worker")

@message_broker.task
async def process_order(order_id: int) -> None:
    logger.info("Обработка заказа... order_id=%s", order_id)
    await asyncio.sleep(2)
    logger.info("Заказ обработан! order_id=%s", order_id)