from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from config.db_config import get_db
from schemas.user import UserCreate, UserLogin, UserResponse, AuthResponse
from crud.user import get_user_by_phone, create_user, create_guest_user
from utils.security import verify_password, create_access_token
from utils.response import validate_login_data, validate_register_data
from utils.response import success

router = APIRouter(prefix="/api/user", tags=["用户"])

# 登录接口
@router.post("/login")
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    validate_login_data(user_data)
    
    user = get_user_by_phone(db, user_data.phone)
    if not user or not verify_password(user_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误"
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    user_response = UserResponse.model_validate(user)
    return success(AuthResponse(user_info=user_response, token=access_token), msg="登录成功")

# 注册接口
@router.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    validate_register_data(user_data)

    if user_data.phone and get_user_by_phone(db, user_data.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号已被注册"
        )
    user = create_user(db, user_data)
    access_token = create_access_token(data={"sub": str(user.id)})
    user_response = UserResponse.model_validate(user)
    return success(AuthResponse(user_info=user_response, token=access_token), msg="注册成功")

@router.post("/guest")
async def guest_login(db: Session = Depends(get_db)):
    user = create_guest_user(db)
    access_token = create_access_token(data={"sub": str(user.id)})
    user_response = UserResponse.model_validate(user)
    return success(AuthResponse(user_info=user_response, token=access_token), msg="登录成功")
