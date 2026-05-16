from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from config.db_config import get_db
from schemas.users import UserCreate, UserLogin, UserResponse, AuthResponse
from crud.users import get_user_by_phone, create_user, create_guest_user, get_user_by_id
from utils.security import verify_password, create_access_token

router = APIRouter(prefix="/api/user", tags=["用户"])

@router.post("/login", response_model=AuthResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = get_user_by_phone(db, user_data.phone)
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误"
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    user_response = UserResponse.model_validate(user)
    return AuthResponse(user_info=user_response, token=access_token)

@router.post("/register", response_model=AuthResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if user_data.phone and get_user_by_phone(db, user_data.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号已被注册"
        )
    user = create_user(db, user_data)
    access_token = create_access_token(data={"sub": str(user.id)})
    user_response = UserResponse.model_validate(user)
    return AuthResponse(user_info=user_response, token=access_token)

@router.post("/guest", response_model=AuthResponse)
async def guest_login(db: Session = Depends(get_db)):
    user = create_guest_user(db)
    access_token = create_access_token(data={"sub": str(user.id)})
    user_response = UserResponse.model_validate(user)
    return AuthResponse(user_info=user_response, token=access_token)
