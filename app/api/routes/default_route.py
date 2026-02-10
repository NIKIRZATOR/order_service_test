from sqlalchemy import text
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user

from app.database.session import get_database as get_db
from app.schemas.auth import UserOut

default_router = APIRouter(tags=["default"])

@default_router.get("/home/database")
async def check_db(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    return {"db_result": result.scalar()}

@default_router.get("/fetch_me", response_model=UserOut)
async def fetch_me(user = Depends(get_current_user)):
    return UserOut(id=user.id, email=user.email)