from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import logging

from app.core.rate_limit import limiter

from app.api.deps import get_current_user
from app.database.session import get_database
from app.database.models.order_model import OrderModel, OrderStatus
from app.schemas import order
from app.schemas.order import OrderCreateIn, OrderPatchIn
from app.services.cache_orders import get_cached_order, set_cached_order
from app.services.rabbit_publisher import publish_new_order


orders_router = APIRouter(tags=["orders"])

# инициализация логгера для заказов
logger = logging.getLogger("orders") 

def order_to_dict(order: OrderModel) -> dict:
    return {
        "id": str(order.id),
        "user_id": order.user_id,
        "items": order.items,
        "total_price": order.total_price,
        "status": order.status.value if hasattr(order.status, "value") else str(order.status),
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


@orders_router.post("/orders/", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_order(
    request: Request,
    data: OrderCreateIn,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    # перебор классов товаров из data
    items_payload = [item.model_dump() for item in data.items]

    order = OrderModel(user_id=user.id, items=items_payload, total_price=data.total_price)
    db.add(order)
    await db.commit()
    await db.refresh(order)

    payload = order_to_dict(order)
    await set_cached_order(order.id, payload)

    logger.info("Заказ создан id=%s user_id=%s total=%s", order.id, order.user_id, order.total_price)
    logger.info("Отправка в RABBITMQ order_id=%s", order.id)

    # добавляем сообщение о новом заказе в очередь rabbitmq
    await publish_new_order(order.id)
    
    return payload


@orders_router.get("/orders/{order_id}/")
@limiter.limit("10/minute")
async def get_order(
    request: Request,
    order_id: UUID,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    cached = await get_cached_order(str(order_id))
    if cached:
        if cached.get("user_id") != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому заказу")
        
        # логируем попадание в кэш
        logger.info("!!!Redis find order with id=%s!!!", order_id)

        return cached
    
    logger.info("!!!Redis not find order with id=%s!!!", order_id)
    
    res = await db.execute(select(OrderModel).where(OrderModel.id == order_id))
    order = res.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    if order.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому заказу")
    
    payload = order_to_dict(order)
    await set_cached_order(str(order.id), payload)
    return payload


@orders_router.patch("/orders/{order_id}/")
@limiter.limit("20/minute")
async def patch_order(
    request: Request,
    order_id: UUID,
    data: OrderPatchIn,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    res = await db.execute(select(OrderModel).where(OrderModel.id == order_id))
    order = res.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    
    if order.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому заказу")
    
    order.status = OrderStatus(data.status)
    await db.commit()
    await db.refresh(order)

    payload = order_to_dict(order)
    await set_cached_order(str(order.id), payload)
    return payload


@orders_router.get("/orders/user/{user_id}/")
@limiter.limit("20/minute")
async def get_user_orders(
    request: Request,
    user_id: int,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    if user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этим заказам")
    
    res = await db.execute(select(OrderModel).
                           where(OrderModel.user_id == user_id).
                           order_by(OrderModel.created_at.desc()))
    
    orders = res.scalars().all()
    return [order_to_dict(o) for o in orders]