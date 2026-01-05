# backend/app/api/v1/users.py
"""
用户相关 API。
"""
from fastapi import APIRouter, Depends

from app.api import deps
from app.api.v1 import schemas
from app.core.responses import success_response
from app.data import models

router = APIRouter()


@router.get("/info", response_model=schemas.ApiResponse)
async def get_user_info(
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    返回当前登录用户信息。
    """
    token = None
    # 这里无法直接获取原始 token，因此仅传递 None
    user_info = schemas.UserInfo(
        userId=str(current_user.id),
        username=current_user.username,
        realName=current_user.username,
        roles=["super_admin"] if current_user.is_superuser else ["user"],
        avatar="https://unpkg.com/@vbenjs/static-source@0.1.7/source/avatar-v1.webp",
        token=token,
    )
    return success_response(user_info.model_dump())
