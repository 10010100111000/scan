
"""
定义数据库的表
"""
from sqlalchemy import Column, Integer, String, DateTime, func, Boolean, ForeignKey

# 导入Base类，它是所有模型的基类
from .base import Base

# --- 新增：User (用户) 表 ---
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    # 密码哈希值, 不是明文
    hashed_password = Column(String, nullable=False) 
    is_active = Column(Boolean, default=True)

#定义"organizations"表的模型
class Organization(Base):
    #数据库中的真实表名
    __tablename__ = "organizations"

    #定义表的字段(列)
    #id : 整数,主键,自动索引
    id = Column(Integer, primary_key=True, index=True)
    #name:字符串,必须唯一,不能为空
    name = Column(String, unique=True, nullable=False)
    # created_at: 时间, 自动使用服务器的当前时间作为默认值
    created_at = Column(DateTime(timezone=True), server_default=func.now())