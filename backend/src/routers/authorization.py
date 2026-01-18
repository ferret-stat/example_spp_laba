from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from src.database.models import User
from src.database.get_db import get_db
from src.database.schemas import LoginRequest
from src.utils.utils import verify_password
from src.utils.jwt_utils import create_access_token
from src.services.loging_service import write_audit

router = APIRouter(prefix="/auth", tags=["auth"])


def _login_by_identifier(identifier: str, password: str, db: Session, request: Request):
    validation = select(User).where(or_(User.phone == identifier, User.email == identifier))
    existing_user = db.execute(validation).scalar_one_or_none()

    if not existing_user:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    if not verify_password(password, existing_user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    if not existing_user.is_active:
        raise HTTPException(status_code=400, detail="Пользователь заблокирован")

    access_token = create_access_token(data={"sub": str(existing_user.id)})
    write_audit(db, request, existing_user.id, action="login", entity="auth")
    return {"access_token": access_token, "token_type": "bearer"}


# вход через JSON
@router.post("/login-json")
async def login_json(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    return _login_by_identifier(login_data.identifier, login_data.password, db, request)


# Swagger
@router.post("/login")
async def login_swagger(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    return _login_by_identifier(form_data.username, form_data.password, db, request)
