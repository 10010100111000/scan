"""
存放所有安全相关的函数, 如密码哈希。
"""
from passlib.context import CryptContext

# 1. 创建一个密码上下文实例
#    我们告诉它, 默认算法是 "bcrypt"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码是否与哈希值匹配"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """将明文密码转换为哈希值"""
    return pwd_context.hash(password)