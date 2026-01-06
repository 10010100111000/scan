from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from app.data import models

class BaseProcessor(ABC):
    """
    处理器基类：定义了处理单个扫描结果的标准接口。
    """
    def __init__(self, db: AsyncSession, task: models.ScanTask):
        self.db = db
        self.task = task
        # 获取关联的 project_id 和 root_asset_id，方便后续入库使用
        self.project_id = task.asset.project_id if task.asset else None
        self.root_asset_id = task.asset_id

    @abstractmethod
    async def process(self, item: dict) -> int:
        """
        处理单条解析后的数据。
        
        :param item: 解析器(Parser)返回的字典数据
        :return: 成功新增/更新的核心数据条数 (用于统计)
        """
        pass