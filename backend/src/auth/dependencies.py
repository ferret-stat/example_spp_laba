import uuid

from jose import jwt, JWTError
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from src.utils.get_env import EnvConfig
from src.database.models import User
from src.database.get_db import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
ALGORITHM = "HS256"

def get_current_user_id(
    token: str = Depends(oauth2_scheme),
) -> uuid.UUID:
    try:
        payload = jwt.decode(
            token,
            EnvConfig.STATIC_TOKEN,
            algorithms=[ALGORITHM]
        )
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401)
        return uuid.UUID(sub)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
    
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False
)

def get_current_user_id_optional(
    token: str | None = Depends(oauth2_scheme_optional),
):
    if not token:
        return None
    try:
        payload = jwt.decode(token, EnvConfig.STATIC_TOKEN, algorithms=[ALGORITHM])
        return uuid.UUID(payload["sub"])
    except Exception:
        return None
    
def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    try:
        payload = jwt.decode(token, EnvConfig.STATIC_TOKEN, algorithms=[ALGORITHM])
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")

    return user