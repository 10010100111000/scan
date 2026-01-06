from .subdomain_processor import SubdomainProcessor
from .port_processor import PortProcessor
from .http_processor import HttpProcessor
from .vuln_processor import VulnProcessor

# 映射 agent_type 到具体的处理器类
PROCESSOR_MAP = {
    "subdomain": SubdomainProcessor,
    "portscan": PortProcessor,
    "http": HttpProcessor,
    "vulnerability": VulnProcessor
}

def get_processor_class(agent_type: str):
    """
    根据任务的 agent_type 获取对应的处理器类
    """
    return PROCESSOR_MAP.get(agent_type)