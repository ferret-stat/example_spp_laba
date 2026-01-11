import uuid

from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Request

from jose import jwt, JWTError
from src.utils.get_env import EnvConfig

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    current_utc_time = datetime.now(timezone.utc)
    if expires_delta:
        expire = current_utc_time + expires_delta
    else:
        expire = current_utc_time + \
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, EnvConfig.STATIC_TOKEN, algorithm=ALGORITHM)

    return encoded_jwt


def get_current_user_id(request: Request) -> uuid.UUID | None:
    auth = request.headers.get("Authorization")
    # Анонимус, для отладки
    # if not auth or not auth.startswith("Bearer "):
    #     return None

    token = auth.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, EnvConfig.STATIC_TOKEN, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            return None
        return uuid.UUID(sub)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")

