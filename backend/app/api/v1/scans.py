# backend/app/api/v1/scans.py
"""
扫描触发相关 API。
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from arq.connections import ArqRedis

from app.api import deps
from app.api.v1 import schemas
from app.core.arq_config import get_arq_pool, TASK_RUN_SCAN, ARQ_QUEUE_NAME
from app.core.config_loader import get_scan_config_by_name, get_scan_strategy_by_name
from app.core.responses import success_response
from app.data import models
from sqlalchemy import func
from sqlalchemy.future import select

router = APIRouter()


@router.post("/assets/{asset_id}/scan", response_model=schemas.ApiResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_scan_for_asset(
    asset_id: int,
    strategy_name: str = Body(..., embed=True, description="要使用的扫描策略名称 (来自 scan_strategies.yaml)"),
    db: AsyncSession = Depends(deps.get_db),
    arq_redis: ArqRedis = Depends(get_arq_pool),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    为一个根资产触发一个新的扫描策略任务（多阶段）。

    需要登录。
    """
    asset = await db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"资产 ID {asset_id} 不存在")

    strategy = get_scan_strategy_by_name(strategy_name)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的扫描策略名称: '{strategy_name}'",
        )

    # 扫描策略由多个“扫描配置名称”组成，按顺序创建多个任务
    # 扫描策略由多个“扫描配置名称”组成，按顺序创建多个任务
    step_names = [step for step in strategy.get("steps", []) if isinstance(step, str)]
    if not step_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"扫描策略 '{strategy_name}' 未包含任何步骤",
        )

    # 扫描去重：如果任意项目已有同名资产的扫描任务，则不重复触发
    normalized_name = asset.name.strip().lower().rstrip(".")
    asset_stmt = select(models.Asset.id).where(func.lower(models.Asset.name) == normalized_name)
    asset_rows = await db.execute(asset_stmt)
    asset_ids = [row[0] for row in asset_rows.all()]
    if asset_ids:
        task_stmt = select(models.ScanTask.id).where(models.ScanTask.asset_id.in_(asset_ids))
        task_rows = await db.execute(task_stmt)
        if task_rows.first():
            response_data = schemas.ScanSubmissionResponse(strategy_name=strategy_name, task_ids=[])
            return success_response(response_data, message="已存在相关扫描结果，未重复触发扫描")

    task_ids: list[int] = []
    for step_name in step_names:
        scan_config = get_scan_config_by_name(step_name)
        if not scan_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"策略步骤引用了无效配置: '{step_name}'",
            )
        db_scan_task = models.ScanTask(
            asset_id=asset_id,
            config_name=step_name,
            status="pending",
        )
        db.add(db_scan_task)
        try:
            await db.commit()
            await db.refresh(db_scan_task)
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建扫描任务失败: {e}")

        try:
            await arq_redis.enqueue_job(
                TASK_RUN_SCAN,
                db_scan_task.id,
                _queue_name=ARQ_QUEUE_NAME,
            )
            print(f"任务 {db_scan_task.id} (配置: {step_name}) 已成功推送到队列 {ARQ_QUEUE_NAME}")
        except Exception as e:
            db_scan_task.status = "failed"
            db_scan_task.log = f"推送到队列失败: {e}"
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"任务已创建但推送到队列失败: {e}",
            )

        task_ids.append(db_scan_task.id)

    response_data = schemas.ScanSubmissionResponse(strategy_name=strategy_name, task_ids=task_ids)
    return success_response(response_data)
