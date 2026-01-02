from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api import deps
from app.data import models

router = APIRouter()

@router.get("/{task_id}", response_model=dict)
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
        
    return {
        "id": task.id,
        "status": task.status,          # pending, running, completed, failed
        "config_name": task.config_name,
        "created_at": task.created_at,
        "completed_at": task.completed_at,
        # 截取日志，避免传输过大
        "log": task.log[-2000:] if task.log else "" 
    }

@router.get("/", response_model=List[dict])
async def list_recent_tasks(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取最近的扫描任务列表
    """
    stmt = select(models.ScanTask).order_by(models.ScanTask.id.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    
    return [
        {
            "id": t.id, 
            "status": t.status, 
            "config_name": t.config_name, 
            "asset_id": t.asset_id,
            "created_at": t.created_at
        } 
        for t in tasks
    ]