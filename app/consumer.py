import asyncio
import json
import logging
from typing import Any, Dict, Optional, Union

import aio_pika

from app.core.config import settings
from app.tasks import message_broker, process_order

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("consumer")


# на случай если контейнер rabbitmq поднимается дольше остальных сервисов
# добавим переподключение
async def conn_withretry():
    while True:
        try:
            conn = await aio_pika.connect_robust(settings.RABBIT_URL)
            print("Consumer подключился к rabbitmq")

            logger.info("1. Consumer подключился к rabbitmq, url=%s", settings.RABBIT_URL)

            return conn
        except Exception as e:
            print(f"Ошибка подключения к rabbitmq: {e}. retry 10 sec")
            await asyncio.sleep(10)


def _parse_payload(raw: str) -> Optional[Dict[str, Any]]:
    try:
        payload: Union[Dict[str, Any], str, int] = json.loads(raw)
    except json.JSONDecodeError:
        return None

    # если пришла JSON-строка, внутри которой ещё один JSON
    if isinstance(payload, str):
        # вариант: "123"
        if payload.isdigit():
            return {"order_id": int(payload)}

        # вариант: "{\"order_id\": 123}"
        try:
            payload2 = json.loads(payload)
            if isinstance(payload2, dict):
                return payload2
        except json.JSONDecodeError:
            return None

        return None

    # вариант: 123
    if isinstance(payload, int):
        return {"order_id": payload}

    # вариант: {"order_id": 123}
    if isinstance(payload, dict):
        return payload

    return None


async def main() -> None:
    await message_broker.startup()
    conn = await conn_withretry()

    try:
        channel = await conn.channel()
        queue = await channel.declare_queue(settings.NEW_ORDER_QUEUE, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    raw = message.body.decode("utf-8")

                    logger.info("2. Сообщение получено =%s", raw)

                    payload = _parse_payload(raw)

                    logger.info("3. Payload декодирован =%s тип =%s", payload, type(payload))

                    if payload is None:
                        print("Невалидный JSON/формат сообщения:", raw)
                        continue

                    order_id = payload.get("order_id")

                    logger.info("4. Извлечен order_id=%s", order_id)

                    if order_id is None:
                        print("Нет order_id в сообщении:", payload)
                        continue

                    try:
                        order_id_int = int(order_id)
                    except (TypeError, ValueError):
                        print("order_id не число:", payload)
                        continue

                    logger.info("5. Отправка задачи в TaskIQ, order_id=%s", order_id)

                    # отправляем задачу в TaskIQ
                    await process_order.kiq(order_id_int)
    finally:
        await message_broker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
