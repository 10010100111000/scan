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
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """获取指定根资产下的子域名，附带 IP 关联信息（分页）"""
    stmt = (
        select(models.Host)
        .where(models.Host.root_asset_id == asset_id)
        .options(selectinload(models.Host.ip_addresses))
        .order_by(models.Host.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    hosts = result.scalars().all()
    return [
        {
            "id": h.id,
            "hostname": h.hostname,
            "status": h.status,
            "created_at": h.created_at,
            "ips": [ip.ip_address for ip in (h.ip_addresses or [])]
        }
        for h in hosts
    ]

# --- 2. 获取 IP 和 端口 (Ports) ---
@router.get("/assets/{asset_id}/ports", response_model=List[dict])
async def get_asset_ports(
    asset_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """获取指定资产下的开放端口 (通过 IP -> Port 链路过滤)"""
    stmt = (
        select(models.Port)
        .options(selectinload(models.Port.ip_address))
        .join(models.IPAddress, models.Port.ip_address_id == models.IPAddress.id)
        .where(models.IPAddress.root_asset_id == asset_id)
        .limit(200)
    )
    result = await db.execute(stmt)
    ports = result.scalars().all()
    
    data = []
    for p in ports:
        if p.ip_address:
            data.append({
                "id": p.id,
                "ip": p.ip_address.ip_address,
                "port": p.port_number,
                "service": p.service_name
            })
    return data

# --- 3. 获取 Web 服务 ---
@router.get("/assets/{asset_id}/web", response_model=List[dict])
async def get_asset_web(
    asset_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    stmt = (
        select(models.HTTPService)
        .join(models.Port, models.HTTPService.port_id == models.Port.id)
        .join(models.IPAddress, models.Port.ip_address_id == models.IPAddress.id)
        .where(models.IPAddress.root_asset_id == asset_id)
        .limit(100)
    )
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
    stmt = (
        select(models.Vulnerability)
        .join(models.HTTPService, models.Vulnerability.http_service_id == models.HTTPService.id, isouter=True)
        .join(models.Port, models.HTTPService.port_id == models.Port.id, isouter=True)
        .join(models.IPAddress, models.Port.ip_address_id == models.IPAddress.id, isouter=True)
        .join(models.Host, models.Vulnerability.host_id == models.Host.id, isouter=True)
        .where(
            (models.IPAddress.root_asset_id == asset_id) |
            (models.Host.root_asset_id == asset_id)
        )
        .limit(100)
    )
    result = await db.execute(stmt)
    vulns = result.scalars().all()
    return [
        {"id": v.id, "name": v.vulnerability_name, "severity": v.severity, "url": v.matched_at}
        for v in vulns
    ]
