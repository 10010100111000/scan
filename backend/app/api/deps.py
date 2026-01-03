# backend/app/api/deps.py
"""
存放所有 FastAPI “依赖项” (Dependencies)
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import AsyncGenerator, Optional

# --- 数据库依赖 ---
from app.data.session import AsyncSessionLocal
from app.data import models

# --- 安全依赖 ---
from fastapi.security import OAuth2PasswordBearer
from app.userManage.security import decode_access_token


# 数据库会话“依赖”
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# 帮助函数: 通过用户名获取用户
async def get_user_by_username(db: AsyncSession, username: str) -> Optional[models.User]:
    result = await db.execute(select(models.User).where(models.User.username == username))
    return result.scalars().first()

# 帮助函数: 检查是否首次运行
async def check_first_run(db: AsyncSession = Depends(get_db)) -> bool:
    """
    检查 'users' 表是否为空。
    """
    result = await db.execute(select(models.User))
    first_user = result.scalars().first()
    return first_user is None

# --- 安全依赖 ---

# 前端调用使用 /api/auth/login，因此这里的 tokenUrl 与之保持一致
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> models.User:
    """
    一个依赖函数, 用于验证 Token 并返回当前 *激活* 的用户。
    所有“受保护”的 API 都必须依赖它。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = await get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
        
    return user
