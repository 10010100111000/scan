# backend/app/api/v1/projects.py
"""
API 路由：用于创建和查询项目 (Projects)
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps # 导入我们的依赖
from app.data import models
from app.api.v1 import schemas # 导入 Pydantic 模型
from app.core.responses import success_response

# 1. 创建另一个 APIRouter
router = APIRouter()


@router.get("", response_model=schemas.ApiResponse)
async def list_projects(
    skip: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(20, ge=1, le=100, description="返回条目数"),
    search: Optional[str] = Query(None, description="按名称模糊搜索"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    分页列出项目，支持名称搜索。
    """
    stmt = select(models.Project)
    if search:
        stmt = stmt.where(models.Project.name.ilike(f"%{search}%"))
    stmt = stmt.order_by(models.Project.id.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return success_response(result.scalars().all())


@router.post("", response_model=schemas.ApiResponse)
async def create_project(
    # --- 关键修复 ---
    # 输入的数据模型应该是 ProjectCreate (只包含 name)
    project_in: schemas.ProjectCreate,
    # --- 结束修复 ---
    
    db: AsyncSession = Depends(deps.get_db),
    # 2. “锁定”这个 API
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    创建一个新的项目 (需要登录)。
    """
    print(f"用户 '{current_user.username}' 正在创建项目...")
    db_project = models.Project(name=project_in.name)
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return success_response(db_project)
