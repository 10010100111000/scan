# backend/app/api/v1/assets.py
"""
API 路由：用于根资产 (Assets)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select # 如果需要查询可以用

from app.api import deps # 导入我们的依赖
from app.data import models
from app.api.v1 import schemas # 导入 Pydantic 模型

# 1. 创建 APIRouter
router = APIRouter()

@router.post("/orgs/{org_id}/assets", response_model=schemas.AssetRead, status_code=status.HTTP_201_CREATED)
async def create_asset_for_org(
    org_id: int, # 路径参数: 从 URL 中获取组织 ID
    asset_in: schemas.AssetCreate, # 请求体: 包含 name 和 type
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user) # 锁定 API
):
    """
    为指定的组织创建一个新的根资产 (例如 "example.com" 或 "1.2.3.0/24")。

    需要登录。
    """
    # 1. 检查组织是否存在
    #    db.get() 是 SQLAlchemy 2.0+ 提供的一个便捷方法, 用于通过主键获取对象
    org = await db.get(models.Organization, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"组织 ID {org_id} 不存在")

    # 2. (V1 暂不实现权限检查)

    # 3. 创建数据库模型实例
    db_asset = models.Asset(
        name=asset_in.name,
        type=asset_in.type,
        organization_id=org_id # 关联到组织
    )

    # 4. 存入数据库
    db.add(db_asset)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        # 可以添加更详细的错误处理, 比如检查是否唯一性约束失败
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"创建资产失败: {e}")

    await db.refresh(db_asset)

    return db_asset

# ... 未来添加 GET /assets, GET /assets/{asset_id} 等 ...