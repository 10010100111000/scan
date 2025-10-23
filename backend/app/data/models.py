"""
定义数据库的表
"""
from sqlalchemy import Column, Integer, String, DateTime, func

# 导入Base类，它是所有模型的基类
from .base import Base

#定义"organizations"表的模型
class Organization(Base):
    #数据库中的真实表名
    __tablename__ = "organizations"

    #定义表的字段(列)
    #id : 整数,主键,自动索引
    id = Column(Integer, primary_key=True, index=True)
    #name:字符串,必须唯一,不能为空
    