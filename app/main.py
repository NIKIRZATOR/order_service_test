import logging
from fastapi import FastAPI

from app.api.routes.auth_route import auth_router
from app.api.routes.orders_route import orders_router
from app.api.routes.default_route import default_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


app = FastAPI(title="Сервис заказов")

app.include_router(auth_router)
app.include_router(orders_router)
app.include_router(default_router)

