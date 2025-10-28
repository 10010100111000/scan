# backend/app/parsers/line_parser.py
"""
通用行解析器 (Line Parser)。
处理每行代表一个值的简单文本输出。
"""
import asyncio
# --- 关键修复：导入 AsyncGenerator ---
from typing import List, Dict, Any, AsyncGenerator
# --- 结束修复 ---
from .base_parser import BaseParser

class LineParser(BaseParser):
    """解析每行一个值的文本输出"""

    # --- 关键修复：使用 AsyncGenerator ---
    async def parse(self, raw_output: str, data_mapping: Dict[str, str]) -> AsyncGenerator[Dict[str, Any], None]:
    # --- 结束修复 ---
        """
        解析原始输出。data_mapping 应该包含一个键, 其值为 "self",
        表示这一行本身应该映射到哪个字段。
        例如: {'hostname': 'self'}
        """
        mapping_field = None
        for key, value in data_mapping.items():
            if value == "self":
                mapping_field = key
                break
        
        if not mapping_field:
            print("警告: LineParser 的 data_mapping 未找到值为 'self' 的键。无法解析。")
            return # 无法解析则直接返回

        lines = raw_output.splitlines()
        for line in lines:
            stripped_line = line.strip()
            if stripped_line: # 忽略空行
                yield {mapping_field: stripped_line}
            # 在处理大量行时给 asyncio 一个喘息的机会
            await asyncio.sleep(0)