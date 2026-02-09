import logging
from sqlalchemy import text
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.routes.auth_route import auth_router
from app.api.routes.orders_route import orders_router

from app.database.session import get_database as get_db
from app.schemas.auth import UserOut


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


app = FastAPI(title="Сервис заказов")

app.include_router(auth_router)
app.include_router(orders_router)

@app.get("/home")
async def get_home():
    return {"status": "ok"}

@app.get("/home/database")
async def check_db(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    return {"db_result": result.scalar()}

@app.get("/fetch_me", response_model=UserOut)
async def fetch_me(user = Depends(get_current_user)):
    return UserOut(id=user.id, email=user.email)