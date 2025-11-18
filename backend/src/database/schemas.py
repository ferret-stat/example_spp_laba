from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from uuid import UUID


class LoginRequest(BaseModel):
    identifier: str = Field(..., description="Email or phone number")
    password: str


class UserCreate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str = Field(..., min_length=8)


class UserOut(BaseModel):
    id: UUID
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True
