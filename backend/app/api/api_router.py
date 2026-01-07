# backend/app/api/api_router.py
"""
API v1 的主路由器
"""
from fastapi import APIRouter

from app.api.v1 import auth, projects, assets, tasks, results, users, scan_configs, scans,stats

api_router = APIRouter()

# === 基础功能 ===
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/user", tags=["user"])


# === 核心资源 (Assets & Projects) ===
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])


# === 核心动作 (Scanning) ===
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])

# [修复] 必须加上 prefix="/scan-strategies"
api_router.include_router(scan_configs.router, prefix="/scan-strategies", tags=["scan-strategies"])


# === 结果与监控 (Results & Tasks) ===
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(results.router, prefix="/results", tags=["results"])

#dashboard获取各种状态
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])