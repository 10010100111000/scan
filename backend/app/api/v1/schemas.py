# backend/app/api/v1/schemas.py
"""
定义 Pydantic 模型 (Schemas), 用于 API 的数据验证和响应。
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

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

class AdminCreate(BaseModel):
    # (修复) 重命名, 用于 /setup 接口
    username: str
    password: str 

class UserRead(BaseModel):
    # "读取" 时, 我们绝不返回密码
    id: int
    username: str
    is_active: bool
    
    class Config:
        orm_mode = True # 兼容 SQLAlchemy 模型

# --- Token (认证) Schemas ---

class Token(BaseModel):
    """
    /login 接口成功后返回的响应
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    解码 token 后得到的数据内容
    """
    username: Optional[str] = None