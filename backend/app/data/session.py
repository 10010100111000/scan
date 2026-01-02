# backend/app/data/session.py
"""
配置数据库的连接和会话管理 (Docker/Local 兼容版)
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 1. 数据库连接字符串
# 优先读取环境变量 DATABASE_URL；若未设置，优先使用 Docker Compose 的 db 主机，
# 再回退本地 localhost，避免容器默认连到不存在的本地数据库。
DOCKER_DEFAULT_DB_URL = "postgresql+asyncpg://pentest_user:kali@db:5432/pentest_db"
LOCAL_DEFAULT_DB_URL = "postgresql+asyncpg://pentest_user:kali@localhost:5432/pentest_db"

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or DOCKER_DEFAULT_DB_URL
    or LOCAL_DEFAULT_DB_URL
)

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
