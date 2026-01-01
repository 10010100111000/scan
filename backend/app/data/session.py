# backend/app/data/session.py
"""
配置数据库的连接和会话管理 (Docker/Local 兼容版)
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 1. 数据库连接字符串
# 逻辑: 优先读取环境变量 DATABASE_URL。
# 如果没有 (比如你在本地直接运行 python main.py), 则使用默认的 localhost 配置。
# 格式: postgresql+asyncpg://用户名:密码@主机:端口/数据库名
# 注意: 生产环境中密码不应硬编码, 这里仅为演示便利。
DEFAULT_DB_URL = "postgresql+asyncpg://pentest_user:kali@localhost:5432/pentest_db"

# Docker Compose 会注入 DATABASE_URL=postgresql+asyncpg://pentest_user:kali@db:5432/pentest_db
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# 2. 创建异步引擎
# echo=True 会在控制台打印所有 SQL 语句, 方便调试 (生产环境建议设为 False)
engine = create_async_engine(DATABASE_URL, echo=False)

# 3. 创建异步会话工厂
# 我们之后将通过它来创建数据库会话
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)