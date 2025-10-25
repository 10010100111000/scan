# backend/app/api/api_router.py
"""
API v1 的主路由器
"""
from fastapi import APIRouter

from app.api.v1 import auth
from app.api.v1 import organizations

api_router = APIRouter()

# 1. 包含“认证”路由 ( /login, /setup )
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# 2. 包含“组织”路由 ( /organizations )
api_router.include_router(organizations.router, prefix="/orgs", tags=["organizations"])

# ... 未来我们在这里添加 /assets, /scans 等 ...