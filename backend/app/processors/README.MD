backend/app/processors/
├── __init__.py              # 工厂模式入口
├── base_processor.py        # 定义所有处理器的标准接口
├── subdomain_processor.py   # 处理 Subfinder 结果
├── port_processor.py        # 处理 Nmap/Naabu 结果
├── http_processor.py        # 处理 httpx 结果 (含 ASN 增强)
└── vuln_processor.py        # 处理 Nuclei 结果