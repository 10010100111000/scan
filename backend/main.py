# backend/main.py

import asyncio
from fastapi import FastAPI
from app.data.session import engine
from app.data.base import Base

# 导入我们刚刚创建的“主 API 路由器”
from app.api.api_router import api_router
# 导入 ARQ 关闭函数
from app.core.arq_config import close_arq_pool

# 1. 创建 FastAPI 应用实例
app = FastAPI(
    title="combo",
    description="个人自残扫描管理平台"
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

# 3. 根路由 (保持不变)
@app.get("/")
def read_root():
    return {"message": "欢迎使用 Lightweight Scanner API"}


# 4. *** 关键改动：包含我们所有的 API 路由 ***
#    所有来自 api_router 的路由, 都会被自动加上 "/api/v1" 的前缀
app.include_router(api_router, prefix="/api/v1")
