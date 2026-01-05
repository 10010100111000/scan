# backend/app/core/config_loader.py
"""
加载扫描器配置与扫描策略配置。
"""
import yaml
from pathlib import Path
from functools import lru_cache
from typing import List, Dict, Any, Optional

# 假设配置文件在 backend/configs/ 目录下
CONFIG_FILE_PATH = Path(__file__).parent.parent.parent / "configs" / "scanners.yaml"
STRATEGY_FILE_PATH = Path(__file__).parent.parent.parent / "configs" / "scan_strategies.yaml"

@lru_cache() # 使用缓存, 避免每次调用都重新读取文件
def load_scan_configs() -> List[Dict[str, Any]]:
    """
    加载并解析 scanners.yaml 文件。
    返回一个包含所有扫描配置字典的列表。
    如果文件不存在或格式错误, 会抛出异常。
    """
    if not CONFIG_FILE_PATH.is_file():
        # 在实际应用中, 可能返回空列表或更友好的错误处理
        raise FileNotFoundError(f"扫描配置文件未找到: {CONFIG_FILE_PATH}")
        
    try:
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            configs = yaml.safe_load(f)
            if not isinstance(configs, list):
                raise ValueError("scanners.yaml 的根结构必须是一个列表")
            # (可以添加更详细的验证, 确保每个配置项包含必要字段)
            return configs
    except yaml.YAMLError as e:
        raise ValueError(f"解析 scanners.yaml 文件失败: {e}")
    except Exception as e:
        raise RuntimeError(f"加载扫描配置时发生错误: {e}")

@lru_cache()
def load_scan_strategies() -> List[Dict[str, Any]]:
    """
    加载并解析 scan_strategies.yaml 文件。
    返回扫描策略列表，供前端选择“扫描策略”。
    """
    if not STRATEGY_FILE_PATH.is_file():
        raise FileNotFoundError(f"扫描策略文件未找到: {STRATEGY_FILE_PATH}")

    try:
        with open(STRATEGY_FILE_PATH, "r", encoding="utf-8") as f:
            strategies = yaml.safe_load(f)
            if not isinstance(strategies, list):
                raise ValueError("scan_strategies.yaml 的根结构必须是一个列表")
            return strategies
    except yaml.YAMLError as e:
        raise ValueError(f"解析 scan_strategies.yaml 文件失败: {e}")
    except Exception as e:
        raise RuntimeError(f"加载扫描策略时发生错误: {e}")

def get_scan_config_by_name(config_name: str) -> Optional[Dict[str, Any]]:
    """
    根据配置名称查找扫描配置。
    """
    configs = load_scan_configs()
    for config in configs:
        if isinstance(config, dict) and config.get("config_name") == config_name:
            return config
    return None

def get_available_scan_config_names() -> List[str]:
    """
    获取所有可用的扫描配置名称列表 (用于 API 返回给前端)。
    """
    configs = load_scan_configs()
    names = []
    for config in configs:
        if isinstance(config, dict) and "config_name" in config:
            names.append(config["config_name"])
    return names

def get_scan_strategy_by_name(strategy_name: str) -> Optional[Dict[str, Any]]:
    """
    根据策略名称查找扫描策略。
    """
    strategies = load_scan_strategies()
    for strategy in strategies:
        if isinstance(strategy, dict) and strategy.get("strategy_name") == strategy_name:
            return strategy
    return None
