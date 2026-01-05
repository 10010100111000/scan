# backend/app/api/v1/scan_configs.py
"""
扫描配置相关 API。
"""
from fastapi import APIRouter, Depends

from app.api import deps
from app.api.v1 import schemas
from app.core.config_loader import load_scan_strategies
from app.core.responses import success_response
from app.data import models

router = APIRouter()


@router.get("/scan-strategies", response_model=schemas.ApiResponse)
async def list_scan_strategies(
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    获取可用的扫描策略列表，供前端选择。
    """
    strategies = load_scan_strategies()
    data = [
        schemas.ScanStrategySummary(
            strategy_name=strategy.get("strategy_name"),
            description=strategy.get("description"),
            steps=strategy.get("steps") or [],
        )
        for strategy in strategies
        if isinstance(strategy, dict) and strategy.get("strategy_name")
    ]
    return success_response(data)
