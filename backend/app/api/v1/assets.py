# backend/app/api/v1/assets.py
"""
API 路由：用于根资产 (Assets) 和触发扫描
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.api import deps # 导入我们的依赖
from app.data import models
from app.api.v1 import schemas # 导入 Pydantic 模型

from app.core.responses import success_response

# 1. 创建 APIRouter
router = APIRouter()

@router.get("/assets", response_model=schemas.ApiResponse)
async def list_assets_global(
    skip: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(20, ge=1, le=200, description="返回条目数"),
    search: Optional[str] = Query(None, description="按资产名称模糊搜索"),
    project_id: Optional[int] = Query(None, description="按项目 ID 过滤（可选）"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    全局资产列表（可选按项目过滤）。
    用于“全局视图”或跨项目检索场景。
    """
    stmt = select(models.Asset)
    if project_id is not None:
        stmt = stmt.where(models.Asset.project_id == project_id)
    if search:
        stmt = stmt.where(models.Asset.name.ilike(f"%{search}%"))
    stmt = stmt.order_by(models.Asset.id.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    assets = result.scalars().all()
    return success_response(assets)

@router.get("/assets/{asset_id}", response_model=schemas.ApiResponse)
async def get_asset_detail(
    asset_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    获取单个资产详情（用于结果页加载资产信息）。
    """
    asset = await db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"资产 ID {asset_id} 不存在")
    return success_response(asset)

@router.get("/assets/search", response_model=schemas.ApiResponse)
async def search_assets_by_name(
    name: str = Query(..., description="??????????"),
    limit: int = Query(10, ge=1, le=100, description="?????"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    ?????????????????????????
    """
    normalized = name.strip().lower().rstrip(".")
    if not normalized:
        return []
    stmt = (
        select(models.Asset, models.Project)
        .join(models.Project, models.Asset.project_id == models.Project.id)
        .where(func.lower(models.Asset.name) == normalized)
        .order_by(models.Asset.id.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    data = [
        schemas.AssetSearchRead(
            id=asset.id,
            name=asset.name,
            type=asset.type,
            project_id=asset.project_id,
            created_at=asset.created_at,
            project_name=project.name,
        )
        for asset, project in rows
    ]
    return success_response(data)


@router.get("/projects/{project_id}/assets", response_model=schemas.ApiResponse)
async def list_assets_for_project(
    project_id: int,
    skip: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(20, ge=1, le=200, description="返回条目数"),
    search: Optional[str] = Query(None, description="按资产名称模糊搜索"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    分页列出指定项目的根资产，支持名称搜索。
    """
    project = await db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"项目 ID {project_id} 不存在")

    stmt = select(models.Asset).where(models.Asset.project_id == project_id)
    if search:
        stmt = stmt.where(models.Asset.name.ilike(f"%{search}%"))
    stmt = stmt.order_by(models.Asset.id.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    assets = result.scalars().all()
    return success_response(assets)

@router.post("/projects/{project_id}/assets", response_model=schemas.ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_asset_for_project(
    project_id: int,
    asset_in: schemas.AssetCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    为指定的项目创建一个新的根资产。
    """
    project = await db.get(models.Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"项目 ID {project_id} 不存在")

    db_asset = models.Asset(
        name=asset_in.name,
        type=asset_in.type,
        project_id=project_id
    )
    db.add(db_asset)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"创建资产失败: {e}")
    await db.refresh(db_asset)
    return success_response(db_asset)

# ... 未来添加 GET /scans, GET /scans/{scan_id} 等 ...
