# backend/app/parsers/nmap_parser.py
import xml.etree.ElementTree as ET
from typing import Dict, Any, AsyncGenerator
from .base_parser import BaseParser

class NmapXmlParser(BaseParser):
    """
    解析 Nmap 的 XML 输出 (-oX)。
    提取主机 IP、开放端口、服务名称等信息。
    """

    async def parse(self, raw_output: str, data_mapping: Dict[str, str]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Nmap XML 解析逻辑。
        Yields:
            {
                "ip": "192.168.1.1",
                "port": 80,
                "protocol": "tcp",
                "service": "http",
                "product": "nginx",
                "version": "1.18.0"
            }
        """
        try:
            # 移除可能的非 XML 头部干扰
            xml_start = raw_output.find('<nmaprun')
            if xml_start == -1:
                return
            clean_xml = raw_output[xml_start:]
            
            root = ET.fromstring(clean_xml)

            # 遍历所有 <host> 节点
            for host in root.findall('host'):
                # 获取 IP 地址
                address = host.find("address[@addrtype='ipv4']")
                if address is None:
                    continue
                ip_addr = address.get('addr')

                # 检查主机状态
                status = host.find('status')
                if status is None or status.get('state') != 'up':
                    continue

                # 遍历 <ports> 下的 <port>
                ports = host.find('ports')
                if ports is None:
                    continue

                for port in ports.findall('port'):
                    state = port.find('state')
                    if state is None or state.get('state') != 'open':
                        continue

                    port_id = int(port.get('portid'))
                    protocol = port.get('protocol')
                    
                    service_elem = port.find('service')
                    service_name = service_elem.get('name') if service_elem is not None else "unknown"
                    product = service_elem.get('product') if service_elem is not None else None
                    version = service_elem.get('version') if service_elem is not None else None

                    # 构建返回字典
                    yield {
                        "ip": ip_addr,
                        "port": port_id,
                        "protocol": protocol,
                        "service": service_name,
                        "product": product,
                        "version": version
                    }

        except ET.ParseError as e:
            print(f"NmapXmlParser XML 解析错误: {e}")
        except Exception as e:
            print(f"NmapXmlParser 未知错误: {e}")