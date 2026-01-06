# backend/app/api/v1/scans.py
"""
扫描触发相关 API。
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from arq.connections import ArqRedis

from app.api import deps
from app.api.v1 import schemas
# 引入新定义的任务常量
from app.core.arq_config import get_arq_pool, TASK_RUN_SCAN, TASK_RUN_STRATEGY, ARQ_QUEUE_NAME
from app.core.config_loader import get_scan_config_by_name, get_scan_strategy_by_name
from app.core.responses import success_response
from app.data import models
from sqlalchemy import func
from sqlalchemy.future import select

router = APIRouter()

async def create_strategy_tasks(
    asset: models.Asset,
    strategy_name: str,
    db: AsyncSession,
    arq_redis: ArqRedis,
    retrigger: bool = False,
) -> schemas.ScanSubmissionResponse:
    """
    根据扫描策略创建多个任务，并推送到队列。
    """
    strategy = get_scan_strategy_by_name(strategy_name)
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的扫描策略名称: '{strategy_name}'",
        )

    step_names = [step for step in strategy.get("steps", []) if isinstance(step, str)]
    if not step_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"扫描策略 '{strategy_name}' 未包含任何步骤",
        )

    # 扫描去重逻辑
    if not retrigger:
        normalized_name = asset.name.strip().lower().rstrip(".")
        asset_stmt = select(models.Asset.id).where(func.lower(models.Asset.name) == normalized_name)
        asset_rows = await db.execute(asset_stmt)
        asset_ids = [row[0] for row in asset_rows.all()]
        if asset_ids:
            task_stmt = select(models.ScanTask.id).where(models.ScanTask.asset_id.in_(asset_ids))
            task_rows = await db.execute(task_stmt)
            if task_rows.first():
                response_data = schemas.ScanSubmissionResponse(strategy_name=strategy_name, task_ids=[])
                return response_data

    task_ids = await create_tasks_for_steps(
        asset=asset,
        step_names=step_names,
        db=db,
        arq_redis=arq_redis,
        retrigger=retrigger,
        log_hint="重试任务：由重新执行策略触发" if retrigger else None,
    )
    return schemas.ScanSubmissionResponse(strategy_name=strategy_name, task_ids=task_ids)


async def create_tasks_for_steps(
    asset: models.Asset,
    step_names: list[str],
    db: AsyncSession,
    arq_redis: ArqRedis,
    retrigger: bool = False,
    log_hint: str | None = None,
) -> list[int]:
    """
    按指定步骤在数据库创建任务 (Pending状态)，
    然后将整个列表作为一个原子操作推送给 Worker。
    """
    task_ids: list[int] = []
    
    # 1. 先在数据库里把所有步骤的任务都创建好
    for step_name in step_names:
        scan_config = get_scan_config_by_name(step_name)
        if not scan_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"策略步骤引用了无效配置: '{step_name}'",
            )
        db_scan_task = models.ScanTask(
            asset_id=asset.id,
            config_name=step_name,
            step_name=step_name,
            stage=scan_config.get("agent_type"),
            status="pending",
            log=log_hint if retrigger else None,
        )
        db.add(db_scan_task)
        try:
            # 每次循环都 commit 确保获取到 task.id
            await db.commit()
            await db.refresh(db_scan_task)
            task_ids.append(db_scan_task.id)
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建扫描任务失败: {e}")

    # 2. [修改核心] 将整个 task_ids 列表作为一个任务推送给 Worker
    # 这样 Worker 就会按顺序执行它们，而不是并行抢占
    if task_ids:
        try:
            await arq_redis.enqueue_job(
                TASK_RUN_STRATEGY, # <--- 使用新任务名
                task_ids,          # <--- 传递 ID 列表
                _queue_name=ARQ_QUEUE_NAME,
            )
            print(f"策略组已推送: {task_ids}")
        except Exception as e:
            # 如果 Redis 推送失败，在这个简单的实现中，数据库里的任务会一直保持 Pending
            # 生产环境可能需要在这里把任务状态改为 Failed
            print(f"推送策略组失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"任务创建成功但推送失败: {e}",
            )

    return task_ids


@router.post("", response_model=schemas.ApiResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_scan_job(
    scan_in: schemas.ScanRequest,  # <--- 使用 Body 接收所有参数
    db: AsyncSession = Depends(deps.get_db),
    arq_redis: ArqRedis = Depends(get_arq_pool),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    创建一个新的扫描作业。
    """
    # 1. 验证资产是否存在
    asset = await db.get(models.Asset, scan_in.asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"资产 ID {scan_in.asset_id} 不存在")

    # 2. 调用原有的任务创建逻辑
    response_data = await create_strategy_tasks(
        asset=asset,
        strategy_name=scan_in.strategy_name,
        db=db,
        arq_redis=arq_redis,
        retrigger=False,
    )

    if response_data.task_ids:
        return success_response(response_data, message="扫描任务已创建")
    
    return success_response(response_data, message="已存在相关扫描结果，未重复触发扫描")