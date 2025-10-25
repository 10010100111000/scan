# backend/app/api/v1/auth.py
"""
API 路由：用于认证 (setup, login)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps # 导入我们的依赖
from app.data import models
from app.api.v1 import schemas # 导入 Pydantic 模型
from app.userManage.security import (
    get_password_hash, 
    verify_password, 
    create_access_token
)

# 1. 创建一个新的 "APIRouter"
#    这就像一个“迷你”的 FastAPI app
router = APIRouter()

@router.post("/setup", response_model=schemas.UserRead)
async def setup_admin_user(
    admin_in: schemas.AdminCreate,
    is_first_run: bool = Depends(deps.check_first_run), # <-- 使用 deps
    db: AsyncSession = Depends(deps.get_db)             # <-- 使用 deps
):
    """
    创建第一个管理员账户。
    这个接口 *只在* 数据库中没有任何用户时才可用。
    """
    if not is_first_run:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="平台已经初始化，无法创建新管理员。",
        )
        
    hashed_password = get_password_hash(admin_in.password)
    db_user = models.User(
        username=admin_in.username,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    print(f"*** 平台初始化成功！管理员 '{db_user.username}' 已创建。 ***")
    return db_user

@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    用户登录以获取 Access Token
    """
    user = await deps.get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}