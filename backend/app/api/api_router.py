# backend/app/api/api_router.py
"""
API v1 的主路由器
"""
from fastapi import APIRouter

from app.api.v1 import auth, projects, assets, tasks, results, users, scan_configs, scans

api_router = APIRouter()

# === 基础功能 ===
# /api/v1/auth
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# /api/v1/user
api_router.include_router(users.router, prefix="/user", tags=["user"])


# === 核心资源 (Assets & Projects) ===
# /api/v1/projects
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])

# [重点修改] /api/v1/assets
# 包含: GET /assets, GET /assets/search, POST /assets
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])


# === 核心动作 (Scanning) ===
# [重点修改] /api/v1/scans
# 包含: POST /scans (触发扫描)
api_router.include_router(scans.router, prefix="/scans", tags=["scans"])

# /api/v1/scan-strategies (策略配置)
api_router.include_router(scan_configs.router, prefix="/scan-strategies", tags=["scan-strategies"])


# === 结果与监控 (Results & Tasks) ===
# /api/v1/tasks (任务状态)
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# /api/v1/results (扫描结果)
api_router.include_router(results.router, prefix="/results", tags=["results"])