lightweight_scanner/
├── backend/
│   ├── .gitignore              # (Git 忽略文件, 稍后添加)
│   ├── requirements.txt        # (依赖清单, 稍后生成)
│   ├── venv/                   # (虚拟环境, 下一步创建)
│   │
│   ├── app/                    # 我们的主代码区
│   │   ├── __init__.py
│   │   ├── api/                # 存放 API 路由
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       └── ... (未来添加 api_assets.py 等)
│   │   │
│   │   ├── core/               # 存放“编排器”和“配置加载”
│   │   │   ├── __init__.py
│   │   │   └── orchestrator.py # (先创建空文件)
│   │   │
│   │   ├── data/               # 存放数据库所有相关
│   │   │   ├── __init__.py
│   │   │   ├── models.py       # (先创建空文件, 下一步用)
│   │   │   ├── repositories/   # 存放数据库“增删改查”逻辑
│   │   │   │   └── __init__.py
│   │   │   └── session.py      # (先创建空文件, 下一步用)
│   │   │
│   │   ├── domain/             # 存放纯粹的“领域实体” (可选, 但推荐)
│   │   │   └── __init__.py
│   │   │
│   │   ├── agents/             # 存放“通用功能”执行器
│   │   │   ├── __init__.py
│   │   │   └── ... (未来添加 subdomain_agent.py 等)
│   │   │
│   │   └── parsers/            # 存放“通用格式”解析器
│   │       ├── __init__.py
│   │       └── ... (未来添加 line_parser.py 等)
│   │
│   ├── configs/                # 存放你的 YAML 配置文件
│   │   └── scanners.yaml       # (先创建空文件, 下一步用)
│   │
│   ├── alembic/                # 数据库“迁移”工具的目录 (下一步生成)
│   │
│   ├── main.py                 # FastAPI Web 应用入口 (先创建空文件)
│   └── worker.py               # ARQ 扫描“工人”入口 (先创建空文件)
│
└── ... (未来还会有 frontend/ 等)