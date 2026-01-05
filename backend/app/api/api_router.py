# backend/app/api/api_router.py
"""
API v1 的主路由器
"""
from fastapi import APIRouter

from app.api.v1 import auth, projects, assets, tasks, results, users, scan_configs, scans

api_router = APIRouter()

# 1. 包含“认证”路由 ( /login, /setup )
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# 用户信息
api_router.include_router(users.router, prefix="/user", tags=["user"])

# 2. 包含“项目”路由 ( /projects )
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])

# 3. *** 新增：包含“资产”路由 ***
api_router.include_router(assets.router, tags=["assets"])
# 扫描策略
api_router.include_router(scan_configs.router, tags=["scan-strategies"])
# 扫描任务触发
api_router.include_router(scans.router, tags=["scans"])
# --- 新增 ---
# 任务状态查询
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# 结果数据查询
api_router.include_router(results.router, prefix="/results", tags=["results"])
