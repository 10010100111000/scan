"""
配置数据库的连接和会话管理
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

#1.数据库连接字符串
DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

#2.创建异步引擎
engine = create_async_engine(DATABASE_URL, echo=True)

#3.创建异步会话工厂
#我们之后将通过它来创建数据库会话
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)