import datetime

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

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

    if user_data.email or user_data.phone:
        existing_user = db.execute(
            text("""
            SELECT id FROM public.users 
            WHERE email = :email OR phone = :phone
            """),
            {
                "email": user_data.email,
                "phone": user_data.phone
            }
        ).fetchone()

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Пользователь с таким email или телефоном уже существует"
            )

    hashed_password = hash_password(user_data.password)

    new_user_id = generate_user_id()
    current_time = datetime.datetime.now()

    db.execute(
        text("""
        INSERT INTO public.users 
        (id, email, phone, hashed_password, is_active, is_superuser, created_at)
        VALUES (:id, :email, :phone, :hashed_password, :is_active, :is_superuser, :created_at)
        """),
        {
            "id": new_user_id,
            "email": user_data.email,
            "phone": user_data.phone,
            "hashed_password": hashed_password,
            "is_active": True,
            "is_superuser": False,
            "created_at": current_time
        }
    )
    db.commit()

    return {
        "id": new_user_id,
        "email": user_data.email,
        "phone": user_data.phone,
        "is_active": True,
        "is_superuser": False
    }
