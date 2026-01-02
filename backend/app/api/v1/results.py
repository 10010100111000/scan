from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, Field

from app.api import deps
from app.data import models

router = APIRouter()


class HostCreatePayload(BaseModel):
    hostname: str = Field(..., description="子域名/主机名", example="app.example.com")
    status: str = Field("discovered", description="状态", example="discovered")
    is_bookmarked: bool = Field(False, description="是否收藏")
    ips: Optional[List[str]] = Field(None, description="可选，关联的 IP 地址列表")


class HostUpdatePayload(BaseModel):
    status: Optional[str] = Field(None, description="状态", example="confirmed")
    is_bookmarked: Optional[bool] = Field(None, description="是否收藏")


def _serialize_host(host: models.Host) -> Dict[str, Any]:
    return {
        "id": host.id,
        "hostname": host.hostname,
        "status": host.status,
        "created_at": host.created_at,
        "ips": [ip.ip_address for ip in (host.ip_addresses or [])],
        "is_bookmarked": host.is_bookmarked,
        "organization_id": host.organization_id,
        "root_asset_id": host.root_asset_id,
    }

# --- 1. 获取子域名 (Hosts) - Cursor Based Pagination ---
@router.get("/assets/{asset_id}/hosts", response_model=Dict[str, Any])
async def get_asset_hosts(
    asset_id: int,
    limit: int = Query(100, ge=1, le=1000),
    cursor: Optional[int] = Query(None, description="Cursor for pagination (last seen host id)."),
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    获取指定根资产下的子域名，支持基于 id 的游标分页（按 id 降序）。
    适用于大量数据的高性能查询。
    """
    real_limit = min(limit, 1000)

    stmt = (
        select(models.Host)
        .where(models.Host.root_asset_id == asset_id)
        .options(selectinload(models.Host.ip_addresses))
    )

    if cursor:
        stmt = stmt.where(models.Host.id < cursor)

    stmt = stmt.order_by(models.Host.id.desc()).limit(real_limit + 1)

    result = await db.execute(stmt)
    hosts = result.scalars().all()

    has_more = len(hosts) > real_limit
    items = hosts[:real_limit]
    next_cursor = items[-1].id if has_more and items else None

    return {
        "items": [
            _serialize_host(h) for h in items
        ],
        "next_cursor": next_cursor,
        "has_more": has_more,
        "limit": real_limit,
    }


@router.get("/assets/{asset_id}/hosts/{host_id}", response_model=Dict[str, Any])
async def get_host_detail(
    asset_id: int,
    host_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    host = await db.get(models.Host, host_id)
    if not host or host.root_asset_id != asset_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    await db.refresh(host, attribute_names=["ip_addresses"])
    return _serialize_host(host)


@router.post("/assets/{asset_id}/hosts", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_host_for_asset(
    asset_id: int,
    payload: HostCreatePayload,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    asset = await db.get(models.Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

    host = models.Host(
        hostname=payload.hostname.lower().rstrip("."),
        status=payload.status,
        is_bookmarked=payload.is_bookmarked,
        organization_id=asset.organization_id,
        root_asset_id=asset.id,
    )
    db.add(host)
    try:
        await db.commit()
        await db.refresh(host)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Host already exists")

    # 可选：创建 IP 关联
    if payload.ips:
        for ip_val in payload.ips:
            existing_ip = await db.execute(select(models.IPAddress).where(models.IPAddress.ip_address == ip_val))
            ip_obj = existing_ip.scalars().first()
            if not ip_obj:
                ip_obj = models.IPAddress(
                    ip_address=ip_val,
                    organization_id=asset.organization_id,
                    root_asset_id=asset.id,
                    status="discovered"
                )
                db.add(ip_obj)
                await db.flush()
            dns_exists = await db.execute(
                select(models.DNSRecord).where(
                    models.DNSRecord.host_id == host.id,
                    models.DNSRecord.ip_address_id == ip_obj.id
                )
            )
            if not dns_exists.scalars().first():
                db.add(models.DNSRecord(host_id=host.id, ip_address_id=ip_obj.id, record_type="A"))
        await db.commit()
        await db.refresh(host, attribute_names=["ip_addresses"])

    return _serialize_host(host)


@router.patch("/assets/{asset_id}/hosts/{host_id}", response_model=Dict[str, Any])
async def update_host_for_asset(
    asset_id: int,
    host_id: int,
    payload: HostUpdatePayload,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    host = await db.get(models.Host, host_id)
    if not host or host.root_asset_id != asset_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")

    if payload.status is not None:
        host.status = payload.status
    if payload.is_bookmarked is not None:
        host.is_bookmarked = payload.is_bookmarked

    await db.commit()
    await db.refresh(host, attribute_names=["ip_addresses"])
    return _serialize_host(host)


@router.delete("/assets/{asset_id}/hosts/{host_id}", response_model=Dict[str, str])
async def delete_host_for_asset(
    asset_id: int,
    host_id: int,
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    host = await db.get(models.Host, host_id)
    if not host or host.root_asset_id != asset_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    await db.delete(host)
    await db.commit()
    return {"detail": "deleted"}

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
