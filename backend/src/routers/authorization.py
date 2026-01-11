from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm

from src.database.models import User
from src.database.get_db import get_db
from src.database.schemas import LoginRequest
from src.utils.utils import verify_password
from src.utils.jwt_utils import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


def _login_by_identifier(identifier: str, password: str, db: Session):
    validation = select(User).where(or_(User.phone == identifier, User.email == identifier))
    existing_user = db.execute(validation).scalar_one_or_none()

    if not existing_user:
        raise HTTPException(status_code=401, detail="Неверный идентификатор или пароль")

    if not verify_password(password, existing_user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный идентификатор или пароль")

    if not existing_user.is_active:
        raise HTTPException(status_code=400, detail="Аккаунт деактивирован")

    access_token = create_access_token(data={"sub": str(existing_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


# Для фронта
@router.post("/login-json")
async def login_json(login_data: LoginRequest, db: Session = Depends(get_db)):
    return _login_by_identifier(login_data.identifier, login_data.password, db)


# Swagger
@router.post("/login")
async def login_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    return _login_by_identifier(form_data.username, form_data.password, db)

