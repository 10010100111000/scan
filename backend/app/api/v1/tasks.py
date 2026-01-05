from typing import Any, List, Optional
from datetime import datetime, timezone
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api import deps
from app.data import models
from app.api.v1 import schemas
from app.data.session import AsyncSessionLocal
from app.core.responses import success_response
from app.api.v1.scans import create_strategy_tasks, create_tasks_for_steps
from app.core.arq_config import get_arq_pool
from app.core.config_loader import load_scan_strategies

router = APIRouter()

@router.get("/", response_model=schemas.ApiResponse)
async def list_recent_tasks(
    skip: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(10, ge=1, le=100, description="返回条目数"),
    status: Optional[str] = Query(None, description="按任务状态过滤"),
    asset_id: Optional[int] = Query(None, description="按资产 ID 过滤"),
    config_name: Optional[str] = Query(None, description="按扫描配置名称过滤"),
    project_id: Optional[int] = Query(None, description="按项目 ID 过滤"),
    created_after: Optional[datetime] = Query(None, description="仅返回在此时间之后创建的任务"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取最近的扫描任务列表
    """
    stmt = select(models.ScanTask).options(selectinload(models.ScanTask.asset).selectinload(models.Asset.project))
    if status:
        stmt = stmt.where(models.ScanTask.status == status)
    if asset_id:
        stmt = stmt.where(models.ScanTask.asset_id == asset_id)
    if config_name:
        stmt = stmt.where(models.ScanTask.config_name == config_name)
    if created_after:
        stmt = stmt.where(models.ScanTask.created_at >= created_after)
    # 项目维度过滤（用于任务中心按项目查看）
    if project_id:
        stmt = (
            stmt.join(models.Asset, models.ScanTask.asset_id == models.Asset.id)
            .where(models.Asset.project_id == project_id)
        )

    stmt = stmt.order_by(models.ScanTask.id.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    
    data = []
    for t in tasks:
        project = t.asset.project if t.asset else None
        data.append(
            schemas.ScanTaskRead(
                id=t.id,
                status=t.status,
                config_name=t.config_name,
                asset_id=t.asset_id,
                project_id=project.id if project else None,
                project_name=project.name if project else None,
                created_at=t.created_at,
                completed_at=t.completed_at,
                log=t.log[-2000:] if t.log else None,
                step_name=t.step_name,
                stage=t.stage,
                artifact_path=t.artifact_path,
            )
        )
    return success_response(data)

# --- SSE: 统一任务状态推送 ---
def _serialize_task(task: models.ScanTask) -> dict:
    return {
        "id": task.id,
        "status": task.status,
        "config_name": task.config_name,
        "asset_id": task.asset_id,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "log": task.log[-2000:] if task.log else None,
    }


def _build_event(event_type: str, data: dict) -> str:
    """
    SSE 统一消息结构：
    {
      "type": "task_status" | "heartbeat",
      "ts": "ISO-8601",
      "data": { ... }
    }
    """
    payload = {
        "type": event_type,
        "ts": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _resolve_strategy_for_task(config_name: str) -> tuple[Optional[str], List[str]]:
    """
    根据任务的 config_name 推断所属策略。
    返回 (strategy_name, steps)。如果未匹配，返回 (None, [])。
    """
    strategies = load_scan_strategies()
    for strategy in strategies:
        if not isinstance(strategy, dict):
            continue
        steps = [step for step in strategy.get("steps", []) if isinstance(step, str)]
        if config_name in steps:
            return strategy.get("strategy_name"), steps
    return None, []


@router.get("/stream")
async def stream_tasks(
    limit: int = Query(50, ge=1, le=100, description="返回任务数量"),
    status: Optional[str] = Query(None, description="按任务状态过滤"),
    asset_id: Optional[int] = Query(None, description="按资产 ID 过滤"),
    config_name: Optional[str] = Query(None, description="按扫描配置名称过滤"),
) -> StreamingResponse:
    """
    SSE 推送任务状态：客户端保持长连接，后端统一发送任务列表与汇总。
    """
    async def event_generator():
        last_hash = ""
        last_emit = 0.0
        while True:
            async with AsyncSessionLocal() as db:
                stmt = select(models.ScanTask)
                if status:
                    stmt = stmt.where(models.ScanTask.status == status)
                if asset_id:
                    stmt = stmt.where(models.ScanTask.asset_id == asset_id)
                if config_name:
                    stmt = stmt.where(models.ScanTask.config_name == config_name)
                stmt = stmt.order_by(models.ScanTask.id.desc()).limit(limit)
                result = await db.execute(stmt)
                tasks = result.scalars().all()

            items = [_serialize_task(task) for task in tasks]
            summary = {
                "total": len(items),
                "pending": len([t for t in items if t["status"] == "pending"]),
                "running": len([t for t in items if t["status"] == "running"]),
                "completed": len([t for t in items if t["status"] == "completed"]),
                "failed": len([t for t in items if t["status"] == "failed"]),
            }

            payload = {"tasks": items, "summary": summary}
            payload_hash = json.dumps(payload, sort_keys=True)
            now = asyncio.get_event_loop().time()

            if payload_hash != last_hash:
                yield _build_event("task_status", payload)
                last_hash = payload_hash
                last_emit = now
            elif now - last_emit >= 15:
                yield _build_event("heartbeat", {})
                last_emit = now

            await asyncio.sleep(3)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{task_id:int}", response_model=schemas.ApiResponse)
async def get_task_status(
    task_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取指定扫描任务的状态和日志 (用于前端轮询)
    """
    stmt = (
        select(models.ScanTask)
        .options(selectinload(models.ScanTask.asset).selectinload(models.Asset.project))
        .where(models.ScanTask.id == task_id)
    )
    result = await db.execute(stmt)
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    project = task.asset.project if task.asset else None
    strategy_name, strategy_steps = _resolve_strategy_for_task(task.config_name)
    step_statuses: list[schemas.ScanTaskStepStatus] = []
    if strategy_steps and task.asset_id:
        steps_stmt = (
            select(models.ScanTask)
            .where(
                models.ScanTask.asset_id == task.asset_id,
                models.ScanTask.config_name.in_(strategy_steps),
            )
            .order_by(models.ScanTask.created_at.desc())
        )
        steps_result = await db.execute(steps_stmt)
        related_tasks = steps_result.scalars().all()
        latest_by_step: dict[str, models.ScanTask] = {}
        for step_task in related_tasks:
            if step_task.config_name not in latest_by_step:
                latest_by_step[step_task.config_name] = step_task
        for step_name in strategy_steps:
            related = latest_by_step.get(step_name)
            step_statuses.append(
                schemas.ScanTaskStepStatus(
                    config_name=step_name,
                    task_id=related.id if related else None,
                    status=related.status if related else None,
                    completed_at=related.completed_at if related else None,
                    stage=related.stage if related else None,
                    artifact_path=related.artifact_path if related else None,
                )
            )
    data = schemas.ScanTaskRead(
        id=task.id,
        status=task.status,          # pending, running, completed, failed
        config_name=task.config_name,
        asset_id=task.asset_id,
        project_id=project.id if project else None,
        project_name=project.name if project else None,
        created_at=task.created_at,
        completed_at=task.completed_at,
        # 截取日志，避免传输过大
        log=task.log[-2000:] if task.log else "",
        strategy_name=strategy_name,
        strategy_steps=strategy_steps or None,
        step_statuses=step_statuses or None,
        current_step=task.config_name,
        step_name=task.step_name,
        stage=task.stage,
        artifact_path=task.artifact_path,
    )
    return success_response(data)


@router.get("/{task_id:int}/artifact")
async def download_task_artifact(
    task_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    下载任务产物（原始输出文件）。
    """
    task = await db.get(models.ScanTask, task_id)
    if not task or not task.artifact_path:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return FileResponse(task.artifact_path, filename=f"task_{task_id}.log")


@router.post("/{task_id:int}/retry", response_model=schemas.ApiResponse, status_code=status.HTTP_202_ACCEPTED)
async def retry_scan_task(
    task_id: int,
    mode: str = Body("strategy", embed=True, description="重试模式：strategy=重新执行策略，step=仅重试当前步骤"),
    db: AsyncSession = Depends(deps.get_db),
    arq_redis: Any = Depends(get_arq_pool),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    重试任务：
    - strategy：按策略重跑全部步骤
    - step：仅重试当前步骤
    """
    task = await db.get(models.ScanTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not task.asset_id:
        raise HTTPException(status_code=400, detail="Task missing asset")

    asset = await db.get(models.Asset, task.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if mode not in ("strategy", "step"):
        raise HTTPException(status_code=400, detail="Invalid retry mode")

    if mode == "step":
        # 仅重试当前步骤：复用单步骤策略逻辑
        task_ids = await create_tasks_for_steps(
            asset=asset,
            step_names=[task.config_name],
            db=db,
            arq_redis=arq_redis,
            retrigger=True,
            log_hint=f"重试任务：由任务 #{task.id} 触发",
        )
        response_data = schemas.ScanSubmissionResponse(strategy_name=task.config_name, task_ids=task_ids)
        return success_response(response_data, message="已触发步骤重试")

    strategy_name, _ = _resolve_strategy_for_task(task.config_name)
    if not strategy_name:
        raise HTTPException(status_code=400, detail="无法识别策略名称")

    response_data = await create_strategy_tasks(
        asset=asset,
        strategy_name=strategy_name,
        db=db,
        arq_redis=arq_redis,
        retrigger=True,
    )
    return success_response(response_data, message="已触发策略重试")
