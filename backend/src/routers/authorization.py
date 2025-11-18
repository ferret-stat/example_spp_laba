from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends

from src.database.get_db import get_db
from src.utils.utils import verify_password
from src.database.schemas import LoginRequest
from src.utils.jwt_utils import create_access_token

router = APIRouter()


@router.post("/login")
async def login_for_access_token(
    login_data: LoginRequest, db: Session = Depends(get_db)
):
    user = db.execute(
        text("""
        SELECT * FROM public.users
        WHERE (email = :identifier OR phone = :identifier)
        """),
        {"identifier": login_data.identifier}
    ).fetchone()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Неверный идентификатор или пароль"
        )

    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Неверный идентификатор или пароль"
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Аккаунт деактивирован")

    access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": access_token, "token_type": "bearer"}
