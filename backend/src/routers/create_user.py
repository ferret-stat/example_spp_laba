import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from src.database.models import User
from src.database.schemas import UserCreate, UserOut
from src.database.get_db import get_db
from src.utils.utils import hash_password, generate_user_id

router = APIRouter()


@router.post(
    "/register",
    response_model=UserOut
)
async def create_new_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    if not user_data.email and not user_data.phone:
        raise HTTPException(
            status_code=400,
            detail="Заполните!!!!"
        )

    conditions = []
    if user_data.email:
        conditions.append(User.email == user_data.email)
    if user_data.phone:
        conditions.append(User.phone == user_data.phone)

    if conditions:
        existing_user = db.scalar(select(User.id).where(or_(*conditions)))

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Пользователь с таким email или телефоном уже существует"
            )

    new_user_id = generate_user_id()

    new_user = User(email=user_data.email,
                    phone=user_data.phone,
                    hashed_password=hash_password(user_data.password))
    db.add(new_user)
    db.commit()

    return {
        "id": new_user_id,
        "email": user_data.email,
        "phone": user_data.phone,
        "is_active": True,
        "is_superuser": False
    }
