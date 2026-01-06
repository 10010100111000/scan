# backend/app/core/orchestrator.py
"""
扫描任务的编排器 (重构版)。
职责：
1. 任务调度与状态管理
2. 进程执行 (Stdin/Stdout)
3. 调度解析器与处理器 (不包含具体入库业务逻辑)
"""
import asyncio
import shlex
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.future import select

from app.data.session import AsyncSessionLocal
from app.data import models
from app.core.config_loader import get_scan_config_by_name

# 导入解析器
from app.parsers.line_parser import LineParser
from app.parsers.json_lines_parser import JsonLinesParser
from app.parsers.nmap_parser import NmapXmlParser 

# 导入处理器工厂
from app.processors import get_processor_class

# --- 解析器注册表 ---
PARSERS = {
    "line_parser": LineParser,
    "json_lines": JsonLinesParser,
    "nmap_xml": NmapXmlParser, 
}

async def run_scan_task_logic(task_id: int):
    print(f"[任务 {task_id}] 开始执行...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. 获取任务信息
            task = await db.get(models.ScanTask, task_id)
            if not task or task.status != 'pending':
                return

            asset = await db.get(models.Asset, task.asset_id)
            if not asset:
                task.status = "failed"
                task.log = "关联资产未找到"
                await db.commit()
                return

            # 2. 更新状态
            task.status = "running"
            await db.commit()

            # 3. 加载配置
            scan_config = get_scan_config_by_name(task.config_name)
            if not scan_config:
                raise ValueError(f"配置 '{task.config_name}' 未找到")

            command_template = scan_config.get("command_template")
            parser_type = scan_config.get("output_parser_type")
            data_mapping = scan_config.get("data_mapping", {})
            agent_type = scan_config.get("agent_type")
            task.stage = agent_type
            await db.commit()

            # 4. 准备输入数据 (Stdin 直传逻辑)
            target_source = scan_config.get("target_source", "root")
            input_data = None
            target_arg = ""

            if target_source == "subdomains":
                stmt = select(models.Host.hostname).where(models.Host.root_asset_id == asset.id)
                result = await db.execute(stmt)
                subdomains = [s for s in result.scalars().all() if s]
                
                if not subdomains:
                    task.status = "completed"
                    task.log = "无子域名数据，跳过执行"
                    await db.commit()
                    return

                input_data = "\n".join(subdomains).encode('utf-8')
                target_arg = "" # Stdin 模式无需命令行参数
            else:
                target_arg = shlex.quote(asset.name)
                input_data = None

            # 5. 执行命令
            command = command_template.format(target=target_arg)
            print(f"[任务 {task_id}] 执行命令: {command}")
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout_bytes, stderr_bytes = await process.communicate(input=input_data)
            stdout = stdout_bytes.decode('utf-8', errors='ignore')
            stderr = stderr_bytes.decode('utf-8', errors='ignore')

            # 保存产物
            artifacts_dir = Path("storage") / "artifacts"
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            artifact_path = artifacts_dir / f"task_{task.id}.log"
            artifact_path.write_text(f"CMD: {command}\n\nSTDOUT:\n{stdout}\n\nSTDERR:\n{stderr}", encoding="utf-8")
            task.artifact_path = str(artifact_path)
            
            # 6. 解析与处理 (解耦核心)
            parser_class = PARSERS.get(parser_type)
            if not parser_class:
                raise ValueError(f"未知解析器: {parser_type}")
            
            # 获取对应的业务处理器
            processor_class = get_processor_class(agent_type)
            processor = processor_class(db, task) if processor_class else None
            
            if not processor:
                print(f"[警告] 未找到类型为 {agent_type} 的处理器，仅保存原始日志")
            
            parser = parser_class()
            results_count = 0
            processed_count = 0
            
            # 统一处理循环
            async for res in parser.parse(stdout, data_mapping):
                processed_count += 1
                
                # A. 始终保存原始结果 (RawScanResult)
                raw = models.RawScanResult(scan_task_id=task.id, data=res)
                db.add(raw)
                
                # B. 调用业务处理器入库
                if processor:
                    added = await processor.process(res)
                    results_count += added
            
            # 7. 完成
            if results_count > 0:
                await db.commit()

            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)
            task.log = f"扫描完成，处理 {processed_count} 条，新增 {results_count} 条数据。"
            await db.commit()
            print(f"[任务 {task_id}] 完成。新增: {results_count}")

        except Exception as e:
            print(f"[任务 {task_id}] 异常: {e}")
            await db.rollback()
            async with AsyncSessionLocal() as error_db:
                task_fail = await error_db.get(models.ScanTask, task_id)
                if task_fail:
                    task_fail.status = "failed"
                    task_fail.log = str(e)
                    await error_db.commit()