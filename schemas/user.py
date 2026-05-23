from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    phone: Optional[str] = None
    nickname: Optional[str] = None

class UserCreate(UserBase):
    password: Optional[str] = None

class UserLogin(BaseModel):
    phone: str
    password: str

class UserResponse(UserBase):
    id: int
    avatar: str
    exp: int
    create_time: datetime

    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AuthResponse(BaseModel):
    user_info: UserResponse
    token: str


