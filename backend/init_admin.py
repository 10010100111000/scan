import asyncio
from app.data.session import AsyncSessionLocal
from app.data.models import User
from app.userManage.security import get_password_hash

async def create_admin():
    async with AsyncSessionLocal() as db:
        user = User(
            username="admin",
            hashed_password=get_password_hash("admin123"), # 密码
            email="admin@example.com",
            is_active=True,
            is_superuser=True
        )
        db.add(user)
        try:
            await db.commit()
            print("✅ 管理员创建成功！账号: admin 密码: admin123")
        except Exception as e:
            print(f"⚠️ 创建失败 (可能已存在): {e}")

asyncio.run(create_admin())
exit() # 退出 Python