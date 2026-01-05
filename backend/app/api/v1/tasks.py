from typing import Any, List, Optional
from datetime import datetime, timezone
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api import deps
from app.data import models
from app.api.v1 import schemas
from app.data.session import AsyncSessionLocal
from app.core.responses import success_response

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
        log=task.log[-2000:] if task.log else ""
    )
    return success_response(data)
