import uuid

from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from src.utils.get_env import EnvConfig



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