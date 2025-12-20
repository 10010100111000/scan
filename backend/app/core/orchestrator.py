# backend/app/core/orchestrator.py
"""
扫描任务的编排器。
负责获取任务、加载配置、调用 Agent(简单版)、调用 Parser、保存结果。
(增强版：增加了 portscan 和 http 的处理逻辑)
"""
import asyncio
import subprocess # 用于运行外部命令
from datetime import datetime, timezone
from typing import Optional, Dict, Any # 导入 Dict, Any
import os # 导入 os 用于创建截图目录
from pathlib import Path # 导入 Path 用于处理路径

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update # 导入 update

# 导入数据库会话和模型
from app.data.session import AsyncSessionLocal
from app.data import models

# 导入配置加载器
from app.core.config_loader import get_scan_config_by_name

# 导入解析器
from app.parsers.line_parser import LineParser
from app.parsers.json_lines_parser import JsonLinesParser

# --- 解析器注册表 ---
PARSERS = {
    "line_parser": LineParser,
    "json_lines": JsonLinesParser,
}

# --- 截图存储根目录 (确保这个目录存在且 worker 有写入权限) ---
# (在生产环境中, 这个路径应该来自配置或环境变量)
SCREENSHOT_BASE_DIR = Path("/var/data/lightweight_scanner/screenshots")


async def _ensure_screenshot_dir(task_id: int):
    """确保特定任务的截图子目录存在"""
    task_screenshot_dir = SCREENSHOT_BASE_DIR / f"task_{task_id}"
    try:
        task_screenshot_dir.mkdir(parents=True, exist_ok=True)
        return str(task_screenshot_dir) # 返回路径字符串
    except OSError as e:
        print(f"错误: 无法创建截图目录 {task_screenshot_dir}: {e}")
        return None # 返回 None 表示创建失败

async def run_scan_task_logic(task_id: int):
    """
    执行单个扫描任务的核心逻辑。
    """
    print(f"[任务 {task_id}] 开始执行...")
    scan_start_time = datetime.now(timezone.utc)
    db: Optional[AsyncSession] = None
    task: Optional[models.ScanTask] = None

    try:
        # 1. 获取数据库会话
        db = AsyncSessionLocal()

        # 2. 获取任务和关联资产信息
        #    使用 joinedload 预加载关联的 Asset 对象, 提高效率
        task_stmt = select(models.ScanTask).options(selectinload(models.ScanTask.asset)).where(models.ScanTask.id == task_id)
        task_result = await db.execute(task_stmt)
        task = task_result.scalars().first()

        if not task:
            print(f"[任务 {task_id}] 错误: 在数据库中未找到任务。")
            return
        if task.status != 'pending':
            print(f"[任务 {task_id}] 警告: 任务状态不是 'pending' ({task.status}), 跳过执行。")
            return

        asset = task.asset # 直接从预加载的关系中获取 Asset
        if not asset:
            # (理论上不应该发生, 因为 ScanTask.asset_id 有外键约束, 但还是检查一下)
            print(f"[任务 {task_id}] 错误: 任务关联的资产不存在。")
            task.status = "failed"
            task.log = "关联资产不存在"
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
        agent_type = scan_config.get("agent_type")

        if not command_template or not parser_type or not agent_type:
            raise ValueError(f"扫描配置 '{task.config_name}' 缺少必要字段")

        # 5. 准备并执行命令
        target = asset.name # V1 简化: 目标是根资产名称
        screenshot_dir_path = None # 初始化截图目录路径

        # --- 特殊处理: 如果是 http 类型且需要截图, 先创建目录 ---
        if agent_type == "http" and "-screenshot" in command_template:
            screenshot_dir_path = await _ensure_screenshot_dir(task.id)
            if not screenshot_dir_path:
                raise RuntimeError("无法创建截图存储目录, 任务中止。")
            print(f"[任务 {task_id}] 截图目录已准备: {screenshot_dir_path}")

        # 准备命令模板的替换字典
        format_args = {
            "target": target,
            "task_id": task.id,
            # 未来可以添加 target_list_file 等
            "screenshot_dir": screenshot_dir_path or "" # 提供截图目录路径
        }
        command = command_template.format(**format_args)

        print(f"[任务 {task_id}] 执行命令: {command}")
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_bytes, stderr_bytes = await process.communicate()
        
        stdout = stdout_bytes.decode('utf-8', errors='ignore')
        stderr = stderr_bytes.decode('utf-8', errors='ignore')
        
        if process.returncode != 0:
            log_message = f"命令执行失败 (返回码: {process.returncode})\n命令: {command}\n错误输出:\n{stderr}"
            raise RuntimeError(log_message)

        print(f"[任务 {task_id}] 命令执行成功。开始解析输出...")
        
        # 6. 解析输出
        parser_class = PARSERS.get(parser_type)
        if not parser_class:
            raise ValueError(f"未知的解析器类型: '{parser_type}'")
        
        parser = parser_class()
        results_count = 0
        processed_items = 0 # 记录实际处理的 item 数量
        
        # --- 根据 agent_type 处理结果 ---
        async for result_dict in parser.parse(stdout, data_mapping):
            processed_items += 1
            if processed_items % 100 == 0: # 每处理 100 条打印一次日志
                 print(f"[任务 {task_id}] 已处理 {processed_items} 条解析结果...")

            if agent_type == "subdomain":
                hostname = result_dict.get("hostname")
                if hostname:
                    existing_host_stmt = select(models.Host).where(models.Host.hostname == hostname)
                    existing_host_result = await db.execute(existing_host_stmt)
                    host = existing_host_result.scalars().first()
                    
                    if not host:
                        new_host = models.Host(
                            hostname=hostname,
                            organization_id=asset.organization_id,
                            root_asset_id=asset.id,
                            status="discovered"
                        )
                        db.add(new_host)
                        results_count += 1
                    else:
                        await db.execute(update(models.Host).where(models.Host.id == host.id).values(updated_at=datetime.now(timezone.utc)))
                        if host.status == 'archived':
                            host.status = 'discovered' # 状态更新会在 commit 时保存

            elif agent_type == "portscan":
                ip_str = result_dict.get("ip_address")
                port_num = result_dict.get("port")
                service_name = result_dict.get("service_name") # 可选

                if ip_str and port_num is not None:
                    # 查找或创建 IPAddress
                    ip_stmt = select(models.IPAddress).where(models.IPAddress.ip_address == ip_str)
                    ip_result = await db.execute(ip_stmt)
                    ip_address_obj = ip_result.scalars().first()
                    
                    if not ip_address_obj:
                        ip_address_obj = models.IPAddress(ip_address=ip_str, status="confirmed") # 端口扫描确认 IP 存活
                        db.add(ip_address_obj)
                        await db.flush() # 需要 flush 来获取 ip_address_obj.id
                        print(f"[任务 {task_id}] 新增 IPAddress: {ip_str}")
                    elif ip_address_obj.status == 'discovered' or ip_address_obj.status == 'archived':
                        ip_address_obj.status = 'confirmed' # 更新状态
                        ip_address_obj.updated_at = datetime.now(timezone.utc)

                    # 查找或创建 Port
                    port_stmt = select(models.Port).where(
                        models.Port.ip_address_id == ip_address_obj.id, 
                        models.Port.port_number == port_num
                    )
                    port_result = await db.execute(port_stmt)
                    port_obj = port_result.scalars().first()

                    if not port_obj:
                        new_port = models.Port(
                            ip_address_id=ip_address_obj.id,
                            port_number=port_num,
                            service_name=service_name # 如果解析器提供了
                        )
                        db.add(new_port)
                        results_count += 1
                        print(f"[任务 {task_id}] 新增 Port: {ip_str}:{port_num}")
                    else:
                        # 更新端口信息 (例如 service_name 可能变化)
                        if service_name and port_obj.service_name != service_name:
                            port_obj.service_name = service_name
                        port_obj.updated_at = datetime.now(timezone.utc)


            elif agent_type == "http":
                url = result_dict.get("url")
                port_num = result_dict.get("port") # 解析器需要提供端口号
                ip_str = result_dict.get("ip_address") # 解析器需要提供 IP
                
                if url and port_num is not None and ip_str:
                    # 1. 找到关联的 Port 对象
                    #    (这假设 portscan 已经运行过并创建了 IP 和 Port)
                    port_obj: Optional[models.Port] = None
                    ip_stmt = select(models.IPAddress).where(models.IPAddress.ip_address == ip_str)
                    ip_result = await db.execute(ip_stmt)
                    ip_address_obj = ip_result.scalars().first()
                    
                    if ip_address_obj:
                        port_stmt = select(models.Port).where(
                            models.Port.ip_address_id == ip_address_obj.id,
                            models.Port.port_number == port_num
                        )
                        port_result = await db.execute(port_stmt)
                        port_obj = port_result.scalars().first()

                    if not port_obj:
                        print(f"[任务 {task_id}] 警告: 未找到 URL '{url}' 对应的端口对象 ({ip_str}:{port_num}), 跳过 HTTPService 保存。")
                        continue # 跳过这个结果

                    # 2. 查找或创建 HTTPService
                    http_stmt = select(models.HTTPService).where(models.HTTPService.url == url)
                    http_result = await db.execute(http_stmt)
                    http_service_obj = http_result.scalars().first()

                    # 准备要更新或创建的数据
                    http_data = {
                        "port_id": port_obj.id,
                        "url": url,
                        "title": result_dict.get("title"),
                        "status_code": result_dict.get("status_code"),
                        "tech": result_dict.get("tech"),
                        "response_headers": result_dict.get("response_headers"),
                        "screenshot_path": result_dict.get("screenshot_path"),
                        "favicon_hash": result_dict.get("favicon_hash"),
                        "ssl_info": result_dict.get("ssl_info"),
                        "updated_at": datetime.now(timezone.utc)
                        # is_bookmarked 保持不变
                    }
                    # 过滤掉 None 值, 避免覆盖数据库中可能已有的旧数据(如果本次扫描未获取到)
                    http_data_filtered = {k: v for k, v in http_data.items() if v is not None}


                    if not http_service_obj:
                        new_http_service = models.HTTPService(**http_data_filtered)
                        db.add(new_http_service)
                        results_count += 1
                        print(f"[任务 {task_id}] 新增 HTTPService: {url}")
                    else:
                        # 使用 update 语句批量更新效率更高, 但这里简化处理
                        for key, value in http_data_filtered.items():
                            setattr(http_service_obj, key, value)

            elif agent_type == "vulnerability":
                # TODO: 实现漏洞数据的查找或创建逻辑
                # 1. 获取 hostname 或 url
                # 2. 根据 hostname/url 查找关联的 Host 或 HTTPService 对象
                # 3. 查找或创建 Vulnerability 对象, 关联 Host/HTTPService ID
                # 4. 更新 Vulnerability 的 severity, details, status, updated_at 等
                hostname = result_dict.get("host")
                vuln_name = result_dict.get("vulnerability_name")
                if hostname and vuln_name:
                    # 简化: 打印日志, 不写入数据库
                    print(f"[任务 {task_id}] 发现漏洞: {vuln_name} on {hostname} (结果未保存)")
                    results_count += 1 # 计入处理数量

            elif agent_type == "web_enum": # 目录扫描结果存入 RawScanResult
                if result_dict:
                    raw_result = models.RawScanResult(
                        scan_task_id=task.id,
                        data=result_dict
                    )
                    db.add(raw_result)
                    results_count += 1
            
            # (未来添加 agent_type == "dns_record" 的处理逻辑)
            
            else:
                 print(f"[任务 {task_id}] 警告: 未知的 agent_type '{agent_type}', 结果未处理。")

        # --- 循环结束后 ---
        print(f"[任务 {task_id}] 解析完成, 共处理 {processed_items} 条原始结果。")

        # 7. 提交数据库更改
        if results_count > 0 or (task.status == 'running'):
            print(f"[任务 {task_id}] 准备提交数据库更改 (新增/更新 {results_count} 条)...")
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)
            task.log = f"扫描成功完成, 处理了 {processed_items} 条原始结果, 新增/更新 {results_count} 条资产记录。"
            try:
                await db.commit()
                print(f"[任务 {task_id}] 数据库已提交, 任务状态更新为 'completed'。")
            except Exception as commit_e:
                await db.rollback() # 提交失败时回滚
                raise RuntimeError(f"提交数据库时出错: {commit_e}") from commit_e
        else:
             print(f"[任务 {task_id}] 未发现新结果或无更改需要提交。")
             # 如果任务不需要 commit (例如无新发现), 也需要标记为 completed
             task.status = "completed"
             task.completed_at = datetime.now(timezone.utc)
             task.log = f"扫描成功完成, 处理了 {processed_items} 条原始结果, 未发现新资产或无更新。"
             await db.commit() # 提交状态更新
             print(f"[任务 {task_id}] 任务状态更新为 'completed'。")


    except Exception as e:
        # 8. 统一错误处理
        print(f"[任务 {task_id}] 执行失败: {e}")
        if db and task and task.status == 'running':
            try:
                await db.rollback() 
                task_for_fail = await db.get(models.ScanTask, task_id) 
                if task_for_fail:
                    task_for_fail.status = "failed"
                    task_for_fail.log = f"执行失败: {str(e)[:1000]}" # 限制日志长度
                    task_for_fail.completed_at = datetime.now(timezone.utc)
                    await db.commit()
                    print(f"[任务 {task_id}] 状态已更新为 'failed'。")
                else:
                    print(f"[任务 {task_id}] 错误: 失败后无法在数据库中重新找到任务。")
            except Exception as db_e:
                print(f"[任务 {task_id}] 错误: 更新任务状态为 'failed' 时也失败了: {db_e}")
    finally:
        # 9. 关闭数据库会话
        if db:
            await db.close()
        scan_duration = datetime.now(timezone.utc) - scan_start_time
        print(f"[任务 {task_id}] 执行结束, 总耗时: {scan_duration}。")