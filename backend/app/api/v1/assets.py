# backend/app/api/v1/assets.py
"""
API 路由：用于根资产 (Assets) 和触发扫描
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query # 导入 Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps # 导入我们的依赖
from app.data import models
from app.api.v1 import schemas # 导入 Pydantic 模型

# 导入 ARQ 配置和扫描配置加载器
from app.core.arq_config import get_arq_pool, TASK_RUN_SCAN, ARQ_QUEUE_NAME
from app.core.config_loader import (
    get_scan_config_by_name,
    get_available_scan_config_names,
    load_scan_configs,
)
from arq.connections import ArqRedis # 导入 ArqRedis 类型提示

# 1. 创建 APIRouter
router = APIRouter()

@router.get("/scan-configs", response_model=list[schemas.ScanConfigSummary])
async def list_scan_configs(
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    获取可用的扫描配置列表，供前端下拉选择。
    """
    configs = load_scan_configs()
    return [
        schemas.ScanConfigSummary(
            name=cfg.get("config_name"),
            agent_type=cfg.get("agent_type"),
            description=cfg.get("description")
        )
        for cfg in configs
        if isinstance(cfg, dict) and cfg.get("config_name")
    ]

@router.get("/projects/{project_id}/assets", response_model=list[schemas.AssetRead])
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
    return assets

@router.post("/projects/{project_id}/assets", response_model=schemas.AssetRead, status_code=status.HTTP_201_CREATED)
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
    return db_asset


# --- 新增：触发扫描的 API ---
@router.post("/assets/{asset_id}/scan", response_model=schemas.ScanTaskRead, status_code=status.HTTP_202_ACCEPTED)
async def trigger_scan_for_asset(
    asset_id: int,
    # 使用 Body(...) 来明确指定 config_name 来自请求体
    config_name: str = Body(..., embed=True, description="要使用的扫描配置名称 (来自 scanners.yaml)"),
    db: AsyncSession = Depends(deps.get_db),
    arq_redis: ArqRedis = Depends(get_arq_pool), # <-- 注入 ARQ 连接池
    current_user: models.User = Depends(deps.get_current_active_user) # 锁定 API
):
    """
    为一个根资产触发一个新的扫描任务。

    需要登录。
    """
    # 1. 检查资产是否存在
    asset = await db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"资产 ID {asset_id} 不存在")
        
    # 2. (V1 暂不实现权限检查)

    # 3. 检查扫描配置是否存在
    scan_config = get_scan_config_by_name(config_name)
    if not scan_config:
        available_configs = get_available_scan_config_names()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"无效的扫描配置名称: '{config_name}'. 可用配置: {available_configs}"
        )

    # 4. 创建 ScanTask 记录
    db_scan_task = models.ScanTask(
        asset_id=asset_id,
        config_name=config_name,
        status="pending" # 初始状态
    )
    db.add(db_scan_task)
    try:
        await db.commit()
        await db.refresh(db_scan_task) # 获取 task_id
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建扫描任务失败: {e}")

    # 5. *** 将任务推送到 ARQ 队列 ***
    #    arq_redis.enqueue_job 会将任务信息发送到 Redis
    #    TASK_RUN_SCAN 是我们告诉 worker 要执行哪个函数的名字
    #    db_scan_task.id 是传递给那个函数的参数
    try:
        await arq_redis.enqueue_job(
            TASK_RUN_SCAN, # 要执行的函数名 (在 worker.py 中定义)
            db_scan_task.id, # 传递给函数的参数: 任务 ID
            _queue_name=ARQ_QUEUE_NAME # 指定队列 (可选, 但推荐)
        )
        print(f"任务 {db_scan_task.id} (配置: {config_name}) 已成功推送到队列 {ARQ_QUEUE_NAME}")
    except Exception as e:
        # 如果推送到队列失败, 我们应该把数据库中的任务状态改回 'failed' 或删除它
        db_scan_task.status = "failed"
        db_scan_task.log = f"推送到队列失败: {e}"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务已创建但推送到队列失败: {e}"
        )

    # 6. 返回创建的任务信息 (状态码 202 Accepted 表示请求已接受, 正在后台处理)
    return db_scan_task

# ... 未来添加 GET /scans, GET /scans/{scan_id} 等 ...
