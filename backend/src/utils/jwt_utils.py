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

