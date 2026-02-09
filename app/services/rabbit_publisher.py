import json
import logging
import aio_pika

from app.core.config import settings

async def publish_new_order(order_id: int) -> None:
    conn = await aio_pika.connect_robust(settings.RABBIT_URL)

    async with conn:
        channel = await conn.channel()

        queue_name = settings.NEW_ORDER_QUEUE
        await channel.declare_queue(queue_name, durable=True)

        message = aio_pika.Message(
            body=json.dumps({"order_id": order_id}).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        logger = logging.getLogger("orders")

        logger.info("RabbitMQ публикация: очередь=%s пол_наг=%s", settings.NEW_ORDER_QUEUE, message.body)

        await channel.default_exchange.publish(message, routing_key=queue_name)

