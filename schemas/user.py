from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    phone: Optional[str] = None
    nickname: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = None
    is_guest: bool = False

class UserLogin(BaseModel):
    phone: str
    password: str

class UserResponse(UserBase):
    id: int
    avatar: Optional[str] = None
    is_guest: bool
    total_score: int
    created_at: datetime

    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AuthResponse(BaseModel):
    user_info: UserResponse
    token: str

class MessageResponse(BaseModel):
    message: str
