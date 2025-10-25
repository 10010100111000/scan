from fastapi import FastAPI,Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

#导入数据库引擎,基类,会话
from app.data.session import engine,AsyncSessionLocal
from app.data.base import Base
from app.data import models

#导入我们为api设计的schemas
from app.api.v1.schemas import OrgCreate,OrgRead,UserCreate,UserRead

#导入安全函数
from app.userManage.security import get_password_hash


#1.创建FastApi应用实例
app = FastAPI(
    title="combo",
    description="个人自残扫描管理平台")

# 2. 定义一个“启动”事件 (它会自动创建 User 和 Organization 表)
@app.on_event("startup")
async def on_startup():
    print("FastAPI 启动中，正在尝试连接数据库并创建表...")
    async with engine.begin() as conn:
        # 这会创建 models.py 中所有继承了 Base 的表
        await conn.run_sync(Base.metadata.create_all)
    print("数据库表检查/创建完毕。")

# 3. 数据库会话“依赖” (Dependency)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
            await session.close()


# 4. 根路由 (Hello World)
@app.get("/")
def read_root():
    return {"message": "欢迎使用 Lightweight Scanner API"}


# 5. 创建用户的 API
@app.post("/api/v1/users", response_model=UserRead)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    创建一个新用户。
    """
    hashed_password = get_password_hash(user_in.password)
    db_user = models.User(
        username=user_in.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


# 6. 创建组织的 API (我们最初的 API)
@app.post("/api/v1/organizations", response_model=OrgRead)
async def create_organization(
    org_in: OrgCreate, 
    db: AsyncSession = Depends(get_db)
):
    """
    创建一个新的组织。
    """
    db_org = models.Organization(name=org_in.name)
    db.add(db_org)
    await db.commit()
    await db.refresh(db_org)
    return db_org