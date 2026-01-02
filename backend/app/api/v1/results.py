from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api import deps
from app.data import models

router = APIRouter()

# --- 1. 获取子域名 (Hosts) ---
@router.get("/assets/{asset_id}/hosts", response_model=List[dict])
async def get_asset_hosts(
    asset_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """获取指定根资产下的所有子域名"""
    stmt = select(models.Host).where(models.Host.root_asset_id == asset_id).order_by(models.Host.id.desc())
    result = await db.execute(stmt)
    hosts = result.scalars().all()
    return [
        {"id": h.id, "hostname": h.hostname, "status": h.status, "created_at": h.created_at} 
        for h in hosts
    ]

# --- 2. 获取 IP 和 端口 (Ports) ---
@router.get("/assets/{asset_id}/ports", response_model=List[dict])
async def get_asset_ports(
    asset_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """获取开放端口 (关联查询)"""
    # 简易实现：查询所有端口，实际应关联 asset_id
    stmt = select(models.Port).options(selectinload(models.Port.ip_address)).limit(200)
    result = await db.execute(stmt)
    ports = result.scalars().all()
    
    data = []
    for p in ports:
        if p.ip_address:
            data.append({
                "id": p.id,
                "ip": p.ip_address.ip_address,
                "port": p.port_number,
                "service": p.service_name,
                "banner": p.product
            })
    return data

# --- 3. 获取 Web 服务 ---
@router.get("/assets/{asset_id}/web", response_model=List[dict])
async def get_asset_web(
    asset_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    stmt = select(models.HTTPService).limit(100)
    result = await db.execute(stmt)
    services = result.scalars().all()
    return [
        {"id": s.id, "url": s.url, "title": s.title, "tech": s.tech, "status": s.status_code}
        for s in services
    ]

# --- 4. 获取漏洞 ---
@router.get("/assets/{asset_id}/vulns", response_model=List[dict])
async def get_asset_vulns(
    asset_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    stmt = select(models.Vulnerability).limit(100)
    result = await db.execute(stmt)
    vulns = result.scalars().all()
    return [
        {"id": v.id, "name": v.vulnerability_name, "severity": v.severity, "url": v.matched_at}
        for v in vulns
    ]