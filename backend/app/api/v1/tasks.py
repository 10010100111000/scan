from typing import Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.data import models
from app.api.v1 import schemas

router = APIRouter()

@router.get("/{task_id}", response_model=schemas.ScanTaskRead)
async def get_task_status(
    task_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取指定扫描任务的状态和日志 (用于前端轮询)
    """
    stmt = select(models.ScanTask).where(models.ScanTask.id == task_id)
    result = await db.execute(stmt)
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return schemas.ScanTaskRead(
        id=task.id,
        status=task.status,          # pending, running, completed, failed
        config_name=task.config_name,
        asset_id=task.asset_id,
        created_at=task.created_at,
        completed_at=task.completed_at,
        # 截取日志，避免传输过大
        log=task.log[-2000:] if task.log else ""
    )

@router.get("/", response_model=List[schemas.ScanTaskRead])
async def list_recent_tasks(
    skip: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(10, ge=1, le=100, description="返回条目数"),
    status: Optional[str] = Query(None, description="按任务状态过滤"),
    asset_id: Optional[int] = Query(None, description="按资产 ID 过滤"),
    config_name: Optional[str] = Query(None, description="按扫描配置名称过滤"),
    created_after: Optional[datetime] = Query(None, description="仅返回在此时间之后创建的任务"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取最近的扫描任务列表
    """
    stmt = select(models.ScanTask)
    if status:
        stmt = stmt.where(models.ScanTask.status == status)
    if asset_id:
        stmt = stmt.where(models.ScanTask.asset_id == asset_id)
    if config_name:
        stmt = stmt.where(models.ScanTask.config_name == config_name)
    if created_after:
        stmt = stmt.where(models.ScanTask.created_at >= created_after)

    stmt = stmt.order_by(models.ScanTask.id.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    
    return [
        schemas.ScanTaskRead(
            id=t.id,
            status=t.status,
            config_name=t.config_name,
            asset_id=t.asset_id,
            created_at=t.created_at,
            completed_at=t.completed_at,
            log=t.log[-2000:] if t.log else None
        )
        for t in tasks
    ]
