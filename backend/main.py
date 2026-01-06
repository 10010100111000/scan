# backend/main.py

import os
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.data.session import engine
from app.data.base import Base

# 导入我们刚刚创建的“主 API 路由器”
from app.api.api_router import api_router
# 导入 ARQ 关闭函数
from app.core.arq_config import close_arq_pool

# 1. 创建 FastAPI 应用实例
app = FastAPI(
  title="combo",
    description="渗透测试扫描管理平台",
    version="1.0.0"  
)

# 允许前端跨域访问 (便于 Docker/本地调试)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins == "*":
    origins = ["*"]
else:
    origins = [origin.strip() for origin in allowed_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

# 2. 定义一个“启动”事件 (保持不变)
@app.on_event("startup")
async def on_startup():
    print("FastAPI 启动中，正在尝试连接数据库并创建表...")
    # 简单重试，防止数据库尚未就绪时立即报错
    retry = 0
    last_err = None
    while retry < 5:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("数据库表检查/创建完毕。")
            break
        except Exception as e:
            last_err = e
            retry += 1
            wait = 2 * retry
            print(f"数据库尚未就绪，{wait}s 后重试 ({retry}/5)... 错误: {e}")
            await asyncio.sleep(wait)
    else:
        raise last_err

# --- 定义一个“关闭”事件 ---
@app.on_event("shutdown")
async def on_shutdown():
    """在 FastAPI 关闭时, 关闭 ARQ 连接池"""
    print("FastAPI 关闭中，正在关闭 ARQ Redis 连接池...")
    await close_arq_pool()
    print("ARQ Redis 连接池已关闭。")

app.include_router(api_router, prefix="/api/v1")

if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    app.mount("/static", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend-static")


@app.get("/", include_in_schema=False)
async def serve_index():
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "欢迎使用 Lightweight Scanner API"}


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """为前端单页应用提供 history 路由的 fallback。"""
    if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path == "openapi.json":
        raise HTTPException(status_code=404)

    requested = FRONTEND_DIST / full_path
    if requested.exists() and requested.is_file():
        return FileResponse(requested)

    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    raise HTTPException(status_code=404, detail="页面不存在")
