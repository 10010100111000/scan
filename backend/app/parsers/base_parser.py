# backend/app/parsers/base_parser.py
"""
定义解析器 (Parser) 的基类/接口。
"""
from abc import ABC, abstractmethod
# --- 关键修复：导入 AsyncGenerator ---
from typing import List, Dict, Any, AsyncGenerator 
# --- 结束修复 ---

class BaseParser(ABC):
    """所有解析器的抽象基类"""

    @abstractmethod
    # --- 关键修复：使用 AsyncGenerator ---
    async def parse(self, raw_output: str, data_mapping: Dict[str, str]) -> AsyncGenerator[Dict[str, Any], None]:
    # --- 结束修复 ---
        """
        解析原始输出字符串。

        Args:
            raw_output: 扫描工具的原始标准输出 (stdout)。
            data_mapping: 来自 scanners.yaml 的 data_mapping 配置, 指导如何提取字段。

        Yields:
            一个字典, 代表一条解析后的记录 (符合我们内部 UDF 的部分结构)。
            使用 AsyncGenerator (yield) 允许处理大量输出而无需一次性加载到内存。
        """
        # 这个 yield {} 只是为了满足抽象方法的要求，并让类型检查器满意
        # 在实际的子类中它会被覆盖掉
        yield {}
        raise NotImplementedError