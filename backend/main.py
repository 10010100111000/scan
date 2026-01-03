# backend/main.py

import os
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.data.session import engine
from app.data.base import Base

# 导入我们刚刚创建的“主 API 路由器”
from app.api.api_router import api_router
# 导入 ARQ 关闭函数
from app.core.arq_config import close_arq_pool

# --- 前端静态资源路径 ---
STATIC_ROOT = Path("/app/static")
INDEX_FILE = STATIC_ROOT / "index.html"

# 1. 创建 FastAPI 应用实例
app = FastAPI(
    title="combo",
    description="个人自残扫描管理平台"
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

# --- 新增：定义一个“关闭”事件 ---
@app.on_event("shutdown")
async def on_shutdown():
    """在 FastAPI 关闭时, 关闭 ARQ 连接池"""
    print("FastAPI 关闭中，正在关闭 ARQ Redis 连接池...")
    await close_arq_pool()
    print("ARQ Redis 连接池已关闭。")

# 3. *** 关键改动：包含我们所有的 API 路由 ***
#    所有来自 api_router 的路由, 都会被自动加上 "/api" 的前缀
app.include_router(api_router, prefix="/api")


# 4. 静态资源托管（前端 SPA）
if (STATIC_ROOT / "assets").exists():
    app.mount("/assets", StaticFiles(directory=STATIC_ROOT / "assets"), name="assets")


def _should_serve_spa(path: str) -> bool:
    """判断请求是否应该回退到前端 SPA。"""
    protected_prefixes = ("api", "docs", "openapi.json")
    return not any(path.startswith(prefix) for prefix in protected_prefixes)


def _spa_response():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return JSONResponse({"message": "欢迎使用 Lightweight Scanner API"}, status_code=200)


@app.get("/", include_in_schema=False)
async def serve_root():
    return _spa_response()


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """
    SPA History 模式回退：对于非 API/文档路径，返回构建后的 index.html。
    """
    if not _should_serve_spa(full_path):
        raise HTTPException(status_code=404, detail="Not Found")

    return _spa_response()
