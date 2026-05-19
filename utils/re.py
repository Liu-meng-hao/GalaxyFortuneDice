import re
from fastapi import HTTPException, status
from schemas.user import UserLogin, UserCreate

def validate_login_data(login_data: UserLogin):
    if not login_data.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号不能为空"
        )
    if not login_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码不能为空"
        )
    if not re.match(r'^1[3-9]\d{9}$', login_data.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号格式错误"
        )
    
    if not len(login_data.password) >= 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度不能小于6位"
        )
    return True

def validate_register_data(register_data: UserCreate):
    if not register_data.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号不能为空"
        )
    if not register_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码不能为空"
        )

    if not register_data.nickname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="昵称不能为空"
        )

    if not re.match(r'^1[3-9]\d{9}$', register_data.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="手机号格式错误"
        )

    if not len(register_data.password) >= 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度不能小于6位"
        )
    return True