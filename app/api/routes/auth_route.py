from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import limiter

from app.core.security import create_access_token, do_hash_password, verify_password
from app.database.models.user_model import UserModel
from app.database.session import get_database
from app.schemas.auth import RegisterIn, TokenOut, UserOut


auth_router = APIRouter(tags=["auth"])

@auth_router.post("/register/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")  # ограничение на регистрацию: 5 запросов в минуту с одного IP
async def register(request: Request, data: RegisterIn, db: AsyncSession = Depends(get_database)):
    res = await db.execute(select(UserModel).where(UserModel.email == data.email))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким email уже существует")

    user = UserModel(email = data.email, hash_password=do_hash_password(data.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserOut(id=user.id, email=user.email)

@auth_router.post("/token/", response_model=TokenOut)
@limiter.limit("5/minute")
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_database)):
    res = await db.execute(select(UserModel).where(UserModel.email == form.username))
    user = res.scalar_one_or_none()

    if not user or not verify_password(form.password, user.hash_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные логин или пароль")

    token = create_access_token(user.id)
    return TokenOut(access_token=token, token_type="bearer")