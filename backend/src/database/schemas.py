from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
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

class FilePageOut(BaseModel):
    minio_object_id: str
    description: Optional[str] = None
    meta: Optional[dict] = None

class FilePageCreate(BaseModel):
    description: Optional[str] = Field(default=None, max_length=20000)
    meta: Optional[dict] = None

class FilePageUpdate(BaseModel):
    description: Optional[str] = Field(default=None, max_length=20000)
    meta: Optional[dict] = None

class CommentOut(BaseModel):
    id: str
    file_id: str
    user_id: Optional[str] = None
    author: Optional[str] = None  
    parent_id: Optional[str] = None
    body: str
    is_deleted: bool
    likes_count: int
    created_at: datetime
    updated_at: datetime

class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    parent_id: Optional[str] = None

class CommentUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)

class LikeIn(BaseModel):
    is_like: bool = True

class LikeOut(BaseModel):
    my_like: Optional[bool] = None
