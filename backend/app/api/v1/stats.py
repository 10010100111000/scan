from typing import Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, case, text

from app.api import deps
from app.core.responses import success_response
from app.data import models

router = APIRouter()

@router.get("/dashboard", summary="获取仪表盘核心指标")
async def get_dashboard_stats(
    db: AsyncSession = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    聚合查询：资产概览、任务状态、漏洞分布、最近趋势
    """
    
    # 1. 资产 KPI
    # 统计总数和在线数 (假设 status='online' 代表在线)
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

    # 3. 趋势分析 (最近 7 天任务数)
    # 使用 generate_series 生成日期序列 (PostgreSQL) 或者在应用层补全
    # 这里演示简单分组查询
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
    
    # 补全日期 (防止某天没数据导致断线)
    trend_dates = []
    trend_values = []
    for i in range(7):
        d = (seven_days_ago + timedelta(days=i)).strftime('%m-%d')
        trend_dates.append(d)
        trend_values.append(trend_map.get(d, 0))

    # 4. 最新资产列表
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
            # 这里先模拟漏洞分布，等你有了 Vulnerability 模型后再替换为真实查询
            "vuln_distribution": [
                {"name": "高危", "value": 5},
                {"name": "中危", "value": 12},
                {"name": "低危", "value": 25},
                {"name": "信息", "value": 50}
            ]
        },
        "lists": {
            "recent_assets": recent_assets
        }
    })