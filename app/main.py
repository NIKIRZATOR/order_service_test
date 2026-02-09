from sqlalchemy import text
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_database as get_db


app = FastAPI(title="Order Service")

@app.get("/home")
async def get_home():
    return {"status": "ok"}

@app.get("/home/database")
async def check_db(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    return {"db_result": result.scalar()}