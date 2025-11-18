from sqlalchemy import text, select, or_
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends

from src.database.models import User
from src.database.get_db import get_db
from src.database.schemas import LoginRequest
from src.utils.utils import verify_password
from src.utils.jwt_utils import create_access_token

router = APIRouter()


@router.post("/login")
async def login_for_access_token(
    login_data: LoginRequest, db: Session = Depends(get_db)
):
    validation = select(User).where(
        or_(
            User.phone == login_data.identifier,
            User.email == login_data.identifier
        )
    )
    existing_user = db.execute(validation).scalar_one_or_none()
    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Неверный идентификатор или пароль"
        )

    if not verify_password(login_data.password, existing_user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Неверный идентификатор или пароль"
        )

    if not existing_user.is_active:
        raise HTTPException(status_code=400, detail="Аккаунт деактивирован")

    access_token = create_access_token(data={"sub": str(existing_user.id)})

    return {"access_token": access_token, "token_type": "bearer"}
