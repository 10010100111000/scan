# backend/app/api/api_router.py
"""
API v1 的主路由器
"""
from fastapi import APIRouter

from app.api.v1 import auth, organizations, assets, tasks, results, users

api_router = APIRouter()

# 1. 包含“认证”路由 ( /login, /setup )
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# 用户信息
api_router.include_router(users.router, prefix="/user", tags=["user"])

# 2. 包含“组织”路由 ( /organizations )
api_router.include_router(organizations.router, prefix="/orgs", tags=["organizations"])

# 3. *** 新增：包含“资产”路由 ***
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
# --- 新增 ---
# 任务状态查询
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# 结果数据查询
api_router.include_router(results.router, prefix="/results", tags=["results"])
