import json
from app.core.config import settings
from app.core.redis import redis_client

def _key(order_id: int) -> str:
    return f"order:{order_id}"

async def get_cached_order(order_id: int) -> dict | None:
    raw = await redis_client.get(_key(order_id))
    return json.loads(raw) if raw else None

async def set_cached_order(order_id: int, data: dict) -> None:
    await redis_client.setex(
        _key(order_id),
        settings.ORDER_CACHE_EXPIRE_SECONDS,
        json.dumps(data, default=str),
    )

async def delete_cached_order(order_id: int) -> None:
    await redis_client.delete(_key(order_id))