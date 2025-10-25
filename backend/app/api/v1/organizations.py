# backend/app/api/v1/organizations.py
"""
API 路由：用于创建项目 (Organizations)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps # 导入我们的依赖
from app.data import models
from app.api.v1 import schemas # 导入 Pydantic 模型

# 1. 创建另一个 APIRouter
router = APIRouter()

@router.post("/organizations", response_model=schemas.OrgRead)
async def create_organization(
    org_in: schemas.OrgRead, 
    db: AsyncSession = Depends(deps.get_db),
    # 2. “锁定”这个 API
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    创建一个新的项目 (需要登录)。
    """
    print(f"用户 '{current_user.username}' 正在创建项目...")
    db_org = models.Organization(name=org_in.name)
    db.add(db_org)
    await db.commit()
    await db.refresh(db_org)
    return db_org