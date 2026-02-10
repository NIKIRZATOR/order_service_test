import asyncio
import logging
from uuid import UUID
from taskiq_redis import RedisStreamBroker
from app.core.config import settings

message_broker = RedisStreamBroker(settings.REDIS_URL)

logger = logging.getLogger("worker")

@message_broker.task
async def process_order(order_id: str) -> None:
    order_uuid = UUID(order_id)

    logger.info("Обработка заказа... order_id=%s", order_uuid)
    print(f"Processing order {order_id}...")

    await asyncio.sleep(2)
    
    logger.info("Заказ обработан! order_id=%s", order_uuid)
    print(f"Order {order_id} processed")