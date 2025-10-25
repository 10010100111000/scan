# backend/app/userManage/security.py
"""
存放所有安全相关的函数, 如密码哈希和 JWT 令牌。
"""
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

# --- 密码哈希 ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码是否与哈希值匹配"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """将明文密码转换为哈希值"""
    return pwd_context.hash(password)


# --- JWT 令牌处理 ---

# 1. 密钥 (必须保密, 随便用一个复杂的字符串)
#    在生产环境中, 这个值应该从环境变量中读取
SECRET_KEY = "your-very-strong-and-secret-key-a0b1c2d3e4f5"
# 2. 令牌算法
ALGORITHM = "HS256"
# 3. 令牌过期时间 (例如 30 天)
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT access token
    :param data: 要编码到令牌中的数据 (通常是 user_id 或 username)
    :param expires_delta: 令牌的过期时间
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    解码 JWT access token
    :param token: 令牌字符串
    :return: 令牌中的数据 (payload) 或 None (如果无效)
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None