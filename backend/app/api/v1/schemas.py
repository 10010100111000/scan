"""
定义 Pydantic 模型 (Schemas), 用于 API 的数据验证和响应。
"""
from pydantic import BaseModel
from datetime import datetime

# --- Organization Schemas ---

class OrgCreate(BaseModel):
    name: str

class OrgRead(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        orm_mode = True # 兼容 SQLAlchemy 模型

# --- User Schemas ---

class UserCreate(BaseModel):
    # "创建" 时, 我们需要明文密码
    username: str
    password: str 

class UserRead(BaseModel):
    # "读取" 时, 我们绝不返回密码
    id: int
    username: str
    is_active: bool
    
    class Config:
        orm_mode = True # 兼容 SQLAlchemy 模型