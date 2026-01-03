# backend/app/api/v1/auth.py
"""
API 路由：用于认证 (setup, login)
"""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps # 导入我们的依赖
from app.data import models
from app.api.v1 import schemas # 导入 Pydantic 模型
from app.userManage.security import (
    get_password_hash, 
    verify_password, 
    create_access_token
)
from app.core.responses import success_response, error_response

# 1. 创建一个新的 "APIRouter"
#    这就像一个“迷你”的 FastAPI app
router = APIRouter()

@router.get("/status", response_model=dict)
async def get_auth_status(
    is_first_run: bool = Depends(deps.check_first_run),
):
    """
    返回认证状态，用于前端判断是否需要展示管理员注册入口。
    """
    return success_response({"first_run": is_first_run})

@router.post("/setup", response_model=dict)
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
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=error_response(
                code=status.HTTP_403_FORBIDDEN,
                message="平台已经初始化，无法创建新管理员。",
            ),
        )

    existing_user = await deps.get_user_by_username(db, admin_in.username)
    if existing_user:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(
                code=status.HTTP_400_BAD_REQUEST,
                message="该用户名已存在，请更换后重试。",
            ),
        )
        
    hashed_password = get_password_hash(admin_in.password)
    db_user = models.User(
        username=admin_in.username,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=True,
        email=admin_in.email,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    print(f"*** 平台初始化成功！管理员 '{db_user.username}' 已创建。 ***")
    return success_response(
        schemas.UserRead.model_validate(db_user).model_dump()
    )

@router.post("/login", response_model=dict)
async def login_for_access_token(
    login_in: schemas.LoginRequest,
    db: AsyncSession = Depends(deps.get_db)
):
    """
    用户登录以获取 Access Token
    """
    user = await deps.get_user_by_username(db, login_in.username)
    if not user or not verify_password(login_in.password, user.hashed_password):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response(
                code=status.HTTP_401_UNAUTHORIZED,
                message="用户名或密码不正确",
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    token_data = schemas.AccessToken(accessToken=access_token)
    return success_response(token_data.model_dump())


@router.post("/forgot", response_model=dict)
async def forgot_password(
    payload: schemas.ForgotPasswordRequest,
    is_first_run: bool = Depends(deps.check_first_run),
):
    """
    忘记密码占位接口。当前未启用邮件找回，只做温馨提示。
    """
    if is_first_run:
        return success_response(message="平台尚未初始化管理员，请先注册管理员账号")
    return success_response(message="暂未开放自助重置密码，请联系管理员处理")


@router.post("/change-password", response_model=dict)
async def change_password(
    payload: schemas.PasswordChangeRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    修改当前登录用户的密码。
    """
    if not verify_password(payload.old_password, current_user.hashed_password):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(
                code=status.HTTP_400_BAD_REQUEST,
                message="原密码不正确",
            ),
        )

    current_user.hashed_password = get_password_hash(payload.new_password)
    db.add(current_user)
    await db.commit()
    return success_response(message="密码修改成功")


@router.post("/logout", response_model=dict)
async def logout():
    """
    由于当前未实现刷新令牌与服务端会话，该接口作为前端退出的占位。
    """
    return success_response(message="已退出登录")


@router.post("/refresh", response_model=dict)
async def refresh_token(
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    重新颁发访问令牌。当前未启用单独的刷新令牌机制，直接基于现有用户颁发新的访问令牌。
    """
    access_token = create_access_token(data={"sub": current_user.username})
    token_data = schemas.AccessToken(accessToken=access_token)
    return success_response(token_data.model_dump())


@router.get("/codes", response_model=dict)
async def get_access_codes(
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    返回当前用户的权限码列表。单管理员场景下返回固定值。
    """
    codes = ["super_admin"] if current_user.is_superuser else ["user"]
    return success_response(codes)
