# backend/app/core/orchestrator.py
"""
扫描任务的编排器。
负责获取任务、加载配置、调用 Agent、调用 Parser、保存结果。
"""
import asyncio
import subprocess # 用于运行外部命令
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# 导入数据库会话和模型
from app.data.session import AsyncSessionLocal
from app.data import models

# 导入配置加载器
from app.core.config_loader import get_scan_config_by_name

# 导入解析器 (我们将动态加载它们)
from app.parsers.line_parser import LineParser
from app.parsers.json_lines_parser import JsonLinesParser

# --- 解析器注册表 ---
# (一个简单的字典, 将 parser_type 映射到解析器类)
PARSERS = {
    "line_parser": LineParser,
    "json_lines": JsonLinesParser,
    # "nmap_xml": NmapXmlParser, # 未来可以添加
}

async def run_scan_task_logic(task_id: int):
    """
    执行单个扫描任务的核心逻辑。
    (这个函数会被 worker.py 调用)
    """
    print(f"[任务 {task_id}] 开始执行...")
    scan_start_time = datetime.now(timezone.utc)
    
    # 1. 获取数据库会话 (Worker 需要自己的会话)
    async with AsyncSessionLocal() as db:
        try:
            # 2. 获取任务和关联资产信息
            task = await db.get(models.ScanTask, task_id)
            if not task:
                print(f"[任务 {task_id}] 错误: 在数据库中未找到任务。")
                return
            if task.status != 'pending': # 避免重复执行
                 print(f"[任务 {task_id}] 警告: 任务状态不是 'pending' ({task.status}), 跳过执行。")
                 return

            asset = await db.get(models.Asset, task.asset_id)
            if not asset:
                print(f"[任务 {task_id}] 错误: 关联的资产 ID {task.asset_id} 未找到。")
                task.status = "failed"
                task.log = "关联资产未找到"
                await db.commit()
                return

            # 3. 更新任务状态为 'running'
            task.status = "running"
            await db.commit()
            print(f"[任务 {task_id}] 状态更新为 'running'。目标: {asset.name}, 配置: {task.config_name}")

            # 4. 加载扫描配置
            scan_config = get_scan_config_by_name(task.config_name)
            if not scan_config:
                raise ValueError(f"扫描配置 '{task.config_name}' 未在 scanners.yaml 中定义")

            command_template = scan_config.get("command_template")
            parser_type = scan_config.get("output_parser_type")
            data_mapping = scan_config.get("data_mapping", {})
            agent_type = scan_config.get("agent_type") # 用于决定如何保存结果

            if not command_template or not parser_type or not agent_type:
                 raise ValueError(f"扫描配置 '{task.config_name}' 缺少必要的字段 (command_template, output_parser_type, agent_type)")

            # 5. 准备并执行命令
            #    (这是一个简化的实现, 没有 agent 抽象, 直接运行命令)
            #    需要替换占位符, 例如 {target}
            target = asset.name # 假设目标就是资产名称
            command = command_template.format(target=target) # 简单的替换
            
            print(f"[任务 {task_id}] 执行命令: {command}")
            
            # 使用 asyncio 运行子进程
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout_bytes, stderr_bytes = await process.communicate()
            
            stdout = stdout_bytes.decode('utf-8', errors='ignore')
            stderr = stderr_bytes.decode('utf-8', errors='ignore')
            
            if process.returncode != 0:
                # 命令执行失败
                log_message = f"命令执行失败 (返回码: {process.returncode})\n命令: {command}\n错误输出:\n{stderr}"
                raise RuntimeError(log_message)

            print(f"[任务 {task_id}] 命令执行成功。开始解析输出...")
            
            # 6. 解析输出
            parser_class = PARSERS.get(parser_type)
            if not parser_class:
                raise ValueError(f"未知的解析器类型: '{parser_type}'")
            
            parser = parser_class()
            results_count = 0
            
            # --- 简化版 V1: 根据 agent_type 决定如何处理结果 ---
            if agent_type == "subdomain":
                async for result_dict in parser.parse(stdout, data_mapping):
                    hostname = result_dict.get("hostname")
                    if hostname:
                        # (简单的去重检查和保存逻辑 - 未来需要移到 Repository)
                        existing_host = await db.execute(
                            select(models.Host).where(models.Host.hostname == hostname)
                        )
                        host = existing_host.scalars().first()
                        
                        if not host:
                            new_host = models.Host(
                                hostname=hostname,
                                organization_id=asset.organization_id, # 归属到同一组织
                                root_asset_id=asset.id, # 关联到根资产
                                status="discovered" # 初始状态
                            )
                            db.add(new_host)
                            results_count += 1
                        else:
                            # 如果已存在, 可以更新 updated_at 或 status
                            host.updated_at = datetime.now(timezone.utc)
                            if host.status == 'archived': # 如果之前是归档, 现在重新发现
                                host.status = 'discovered'

            elif agent_type == "web_enum": # 目录扫描结果存入 RawScanResult
                 async for result_dict in parser.parse(stdout, data_mapping):
                     if result_dict: # 确保解析器返回了有效字典
                         raw_result = models.RawScanResult(
                             scan_task_id=task.id,
                             data=result_dict # 直接存入 JSON
                         )
                         db.add(raw_result)
                         results_count += 1

            # (未来添加 agent_type == "portscan", "http", "vulnerability" 的处理逻辑)
            else:
                 print(f"[任务 {task_id}] 警告: 未知的 agent_type '{agent_type}', 结果未处理。")

            # 批量提交数据库更改
            if results_count > 0:
                print(f"[任务 {task_id}] 解析完成, 准备提交 {results_count} 条结果到数据库...")
                await db.commit() # 提交所有添加/更新
                print(f"[任务 {task_id}] 结果已提交。")
            else:
                 print(f"[任务 {task_id}] 解析完成, 未发现新结果或无结果需要提交。")

            # 7. 更新任务状态为 'completed'
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)
            task.log = f"扫描成功完成, 处理了 {results_count} 条结果。" # 简单的日志
            await db.commit()
            print(f"[任务 {task_id}] 状态更新为 'completed'。")

        except Exception as e:
            # 8. 统一错误处理
            print(f"[任务 {task_id}] 执行失败: {e}")
            if 'db' in locals() and db.is_active: # 确保会话仍然可用
                try:
                    # 尝试回滚之前的更改 (例如 status='running')
                    await db.rollback() 
                    # 重新获取 task 对象 (如果之前的 session 无效了)
                    task_for_fail = await db.get(models.ScanTask, task_id) 
                    if task_for_fail:
                         task_for_fail.status = "failed"
                         task_for_fail.log = f"执行失败: {e}"
                         task_for_fail.completed_at = datetime.now(timezone.utc)
                         await db.commit()
                         print(f"[任务 {task_id}] 状态已更新为 'failed'。")
                    else:
                         print(f"[任务 {task_id}] 错误: 失败后无法在数据库中重新找到任务。")
                except Exception as db_e:
                    print(f"[任务 {task_id}] 错误: 更新任务状态为 'failed' 时也失败了: {db_e}")
                    # 这里可能需要更强的日志记录
        finally:
            scan_duration = datetime.now(timezone.utc) - scan_start_time
            print(f"[任务 {task_id}] 执行结束, 总耗时: {scan_duration}。")