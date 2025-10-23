"""
一个'基类'模块，所有的数据表(模型) 都应该从这里导入Base类
这能让sqlalchemy更好地管理模型和数据库之间的映射关系
"""
from sqlalchemy.orm import declarative_base

#创建一个"声明性的基类",所有的模型(models.py)都会导入并继承它
Base = declarative_base()