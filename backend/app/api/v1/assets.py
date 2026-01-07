# backend/app/api/v1/assets.py
"""
API 路由：用于根资产 (Assets) 管理
路径前缀: /assets
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.exc import DBAPIError, IntegrityError, StatementError

from app.api import deps
from app.data import models
from app.api.v1 import schemas
from app.core.responses import success_response

router = APIRouter()

# 1. 列表查询 (GET /)
# 整合了 "全局列表" 和 "项目资产列表" 的功能
@router.get("", response_model=schemas.ApiResponse)
async def list_assets(
    skip: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(20, ge=1, le=200, description="返回条目数"),
    search: Optional[str] = Query(None, description="按资产名称模糊搜索"),
    asset_type: Optional[schemas.AssetTypeLiteral] = Query(None, alias="type", description="按资产类型过滤"),
    project_id: Optional[int] = Query(None, description="按项目 ID 过滤"), # <--- 核心：通过参数过滤
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    获取资产列表。
    - 如果不传 project_id：返回所有资产（全局视图）。
    - 如果传 project_id：返回该项目下的资产（项目视图）。
    """
    stmt = select(models.Asset)
    
    # 动态过滤
    if project_id is not None:
        stmt = stmt.where(models.Asset.project_id == project_id)
        
    if search:
        stmt = stmt.where(models.Asset.name.ilike(f"%{search}%"))

    if asset_type is not None:
        stmt = stmt.where(models.Asset.type == asset_type)
        
    stmt = stmt.order_by(models.Asset.id.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    assets = result.scalars().all()
    data = [schemas.AssetRead.model_validate(asset) for asset in assets]
    return success_response(data)


# 2. 创建资产 (POST /)
# 以前是 POST /projects/{id}/assets，现在改为标准的 POST /assets
@router.post("", response_model=schemas.ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    asset_in: schemas.AssetCreate, # <--- project_id 现在包含在这里面
    response: Response,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    创建一个新的资产。
    """
    # 1. 检查项目是否存在
    project = await db.get(models.Project, asset_in.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"项目 ID {asset_in.project_id} 不存在")

    # 2. 名称标准化
    normalized_name = asset_in.name.strip().lower().rstrip(".")
    if not normalized_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="资产名称不能为空")

    # 3. 检查去重 (同一项目下不重复)
    existing_stmt = (
        select(models.Asset)
        .where(models.Asset.project_id == asset_in.project_id)
        .where(func.lower(models.Asset.name) == normalized_name)
    )
    existing_result = await db.execute(existing_stmt)
    existing_asset = existing_result.scalars().first()
    
    if existing_asset:
        # 如果已存在，返回 200 OK 和现有对象
        response.status_code = status.HTTP_200_OK
        return success_response(
            schemas.AssetRead.model_validate(existing_asset),
            message="资产已存在，已复用现有记录",
        )

    # 4. 创建新记录
    db_asset = models.Asset(
        name=normalized_name,
        type=asset_in.type,
        project_id=asset_in.project_id 
    )
    db.add(db_asset)
    
    try:
        await db.commit()
        await db.refresh(db_asset)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建资产失败: {str(e)}")
        
    return success_response(schemas.AssetRead.model_validate(db_asset))


# 3. 搜索 (GET /search) - 保持不变
@router.get("/search", response_model=schemas.ApiResponse)
async def search_assets_by_name(
    name: str = Query(..., description="按资产名称精确搜索"),
    limit: int = Query(10, ge=1, le=100, description="返回条目数"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    跨项目按资产名称精确搜索（用于扫描去重与复用）。
    """
    normalized = name.strip().lower().rstrip(".")
    if not normalized:
        return success_response([])
        
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


# 4. 详情 (GET /{id}) 
@router.get("/{asset_id}", response_model=schemas.ApiResponse)
async def get_asset_detail(
    asset_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    asset = await db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"资产 ID {asset_id} 不存在")
    return success_response(schemas.AssetRead.model_validate(asset))


# 5. 删除 (DELETE /{id}) 
# -----------------------------------------------------------------------------
# 5. 删除接口 (AssetsView)
# -----------------------------------------------------------------------------
@router.delete("/{asset_id}", summary="删除资产", response_model=schemas.ApiResponse)
async def delete_asset(
    asset_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    asset = await db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    await db.delete(asset)
    await db.commit()
    return success_response(msg="Asset deleted successfully")
