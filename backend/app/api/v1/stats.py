from typing import Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, case

from app.api import deps
from app.core.responses import success_response
from app.data import models

router = APIRouter()

@router.get("/dashboard", summary="获取仪表盘聚合统计数据")
async def get_dashboard_stats(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    聚合查询：资产概览、任务状态、漏洞分布、最近趋势
    """
    
    # 1. 资产 KPI
    # 统计总数和在线数 (假设 status='online' 代表在线)
    # 你的 Asset 模型没有 status 字段，通常用 Host 的 status 或 IPAddress 的 status
    # 这里我们统计总资产数和 IP 数作为示例
    assets_res = await db.execute(
        select(
            func.count(models.Asset.id).label("total"),
            func.count(case((models.Asset.type == 'domain', 1))).label("domains"),
            func.count(case((models.Asset.type == 'cidr', 1))).label("cidrs")
        )
    )
    assets_data = assets_res.one()

    # 2. 任务 KPI
    # 统计 今日完成、正在运行、排队中
    today_start = datetime.now().date()
    tasks_res = await db.execute(
        select(
            func.count(case((models.ScanTask.status == 'running', 1))).label("running"),
            func.count(case((models.ScanTask.status == 'pending', 1))).label("pending"),
            func.count(case((
                (models.ScanTask.status == 'completed') & 
                (models.ScanTask.completed_at >= today_start), 1
            ))).label("completed_today")
        )
    )
    tasks_data = tasks_res.one()

    # 3. 漏洞分布 (Nuclei 真数据!)
    # 直接从 Vulnerability 表聚合查询
    vulns_stmt = select(
        models.Vulnerability.severity, 
        func.count(models.Vulnerability.id)
    ).group_by(models.Vulnerability.severity)
    
    vulns_res = await db.execute(vulns_stmt)
    
    # 数据库查出来的是 [('high', 10), ('low', 5)...]
    # 我们把它转成字典 {'high': 10, 'low': 5}
    real_vuln_counts = {row.severity: row.count for row in vulns_res}
    
    # 转换为前端 ECharts 需要的格式 List[{name, value}]
    # 并且我们可以做一个映射，把英文 severity 翻译成中文，或者保持原样
    vuln_distribution = []
    for severity, count in real_vuln_counts.items():
        vuln_distribution.append({
            "name": severity, # 如 "critical", "high"
            "value": count
        })
        
    # 如果数据库是空的，为了不让图表空着，可以给个默认空列表，前端会显示无数据
    if not vuln_distribution:
         vuln_distribution = [{"name": "暂无漏洞", "value": 0}]

    # 4. 趋势分析 (最近 7 天任务数)
    seven_days_ago = datetime.now() - timedelta(days=6)
    trend_stmt = (
        select(
            func.to_char(models.ScanTask.created_at, 'MM-DD').label("date"),
            func.count(models.ScanTask.id).label("count")
        )
        .where(models.ScanTask.created_at >= seven_days_ago)
        .group_by("date")
        .order_by("date")
    )
    trend_res = await db.execute(trend_stmt)
    trend_map = {row.date: row.count for row in trend_res.all()}
    
    trend_dates = []
    trend_values = []
    for i in range(7):
        d = (seven_days_ago + timedelta(days=i)).strftime('%m-%d')
        trend_dates.append(d)
        trend_values.append(trend_map.get(d, 0))

    # 5. 最新资产列表
    recent_res = await db.execute(
        select(models.Asset).order_by(models.Asset.id.desc()).limit(5)
    )
    recent_assets = [
        {"id": a.id, "name": a.name, "type": a.type, "created_at": a.created_at} 
        for a in recent_res.scalars().all()
    ]

    return success_response({
        "kpi": {
            "assets_total": assets_data.total,
            "assets_domains": assets_data.domains,
            "tasks_running": tasks_data.running,
            "tasks_pending": tasks_data.pending,
            "tasks_completed_today": tasks_data.completed_today
        },
        "charts": {
            "trend_dates": trend_dates,
            "trend_values": trend_values,
            "vuln_distribution": vuln_distribution # <--- 这里使用的是真数据
        },
        "lists": {
            "recent_assets": recent_assets
        }
    })