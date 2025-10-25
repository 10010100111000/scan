# backend/main.py

from fastapi import FastAPI
from app.data.session import engine
from app.data.base import Base

# 导入我们刚刚创建的“主 API 路由器”
from app.api.api_router import api_router


# 1. 创建 FastAPI 应用实例
app = FastAPI(
    title="combo",
    description="个人自残扫描管理平台"
)

# 2. 定义一个“启动”事件 (保持不变)
@app.on_event("startup")
async def on_startup():
    print("FastAPI 启动中，正在尝试连接数据库并创建表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表检查/创建完毕。")


# 3. 根路由 (保持不变)
@app.get("/")
def read_root():
    return {"message": "欢迎使用 Lightweight Scanner API"}


# 4. *** 关键改动：包含我们所有的 API 路由 ***
#    所有来自 api_router 的路由, 都会被自动加上 "/api/v1" 的前缀
app.include_router(api_router, prefix="/api/v1")