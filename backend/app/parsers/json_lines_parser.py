# backend/app/parsers/json_lines_parser.py
"""
通用 JSON Lines 解析器 (.jsonl)。
处理每行一个 JSON 对象的输出格式。
支持使用 "点符号" (dot notation) 进行嵌套字段映射。
"""
import json
import asyncio
# --- 关键修复：导入 AsyncGenerator ---
from typing import List, Dict, Any, AsyncGenerator, Optional
# --- 结束修复 ---
from json import JSONDecodeError
from .base_parser import BaseParser

# 辅助函数，用于通过点符号访问嵌套字典
def _get_nested_value(data: Dict[str, Any], key_path: str) -> Optional[Any]:
    keys = key_path.split('.')
    value = data
    try:
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else: # 如果中间路径不是字典, 则无法继续访问
                return None
            if value is None: # 如果 get() 返回 None, 提前退出
                return None
        return value
    except Exception: # 捕获可能的 AttributeError 等
        return None


class JsonLinesParser(BaseParser):
    """解析 JSON Lines 格式的输出"""

    # --- 关键修复：使用 AsyncGenerator ---
    async def parse(self, raw_output: str, data_mapping: Dict[str, str]) -> AsyncGenerator[Dict[str, Any], None]:
    # --- 结束修复 ---
        """
        解析原始输出。data_mapping 定义了如何从 JSON 对象映射到目标字段。
        支持点符号, 例如: {'severity': 'info.severity'}
        如果 data_mapping 中某个值为 'self', 则将整个 JSON 对象映射到对应键。
        """
        lines = raw_output.splitlines()
        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue # 跳过空行

            try:
                data = json.loads(stripped_line)
                if not isinstance(data, dict):
                    print(f"警告: JsonLinesParser 跳过非字典行: {stripped_line}")
                    continue

                parsed_record: Dict[str, Any] = {}
                for target_field, source_path in data_mapping.items():
                    if source_path == "self":
                        parsed_record[target_field] = data
                    else:
                        value = _get_nested_value(data, source_path)
                        if value is not None: 
                            parsed_record[target_field] = value
                
                if parsed_record: 
                    yield parsed_record

            except JSONDecodeError:
                print(f"警告: JsonLinesParser 无法解析 JSON 行: {stripped_line}")
            except Exception as e:
                print(f"错误: JsonLinesParser 在处理行时出错: {stripped_line}, 错误: {e}")
            
            await asyncio.sleep(0)