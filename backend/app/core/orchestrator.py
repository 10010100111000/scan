# backend/app/core/orchestrator.py
"""
扫描任务的编排器 (完整版)。
负责获取任务、执行命令、解析结果并存入数据库。
支持 Web 安全专注流程：Subfinder (被动) -> Nmap (主动) -> httpx (主动) -> Nuclei (主动)
"""
import asyncio
from urllib.parse import urlparse
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.data.session import AsyncSessionLocal
from app.data import models
from app.core.config_loader import get_scan_config_by_name

# 导入解析器
from app.parsers.line_parser import LineParser
from app.parsers.json_lines_parser import JsonLinesParser
# 注意: 你需要确保 backend/app/parsers/nmap_parser.py 文件存在
from app.parsers.nmap_parser import NmapXmlParser 

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
            if not task:
                print(f"[任务 {task_id}] 未找到")
                return
            if task.status != 'pending':
                print(f"[任务 {task_id}] 状态不为 pending，跳过")
                return

            asset = await db.get(models.Asset, task.asset_id)
            if not asset:
                task.status = "failed"
                task.log = "关联资产未找到"
                await db.commit()
                return

            # 2. 更新状态为 running
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

            # 4. 构造并执行命令
            #    对于 Web 扫描，目标通常是域名 (example.com)
            #    对于 端口 扫描，目标可能是域名或网段 (1.1.1.0/24)
            target = asset.name 
            command = command_template.format(target=target)
            
            print(f"[任务 {task_id}] 执行命令: {command}")
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout_bytes, stderr_bytes = await process.communicate()
            stdout = stdout_bytes.decode('utf-8', errors='ignore')
            stderr = stderr_bytes.decode('utf-8', errors='ignore')
            
            # 简单错误检查 (有些工具如 subfinder即使成功 stderr 也有内容，需谨慎)
            if process.returncode != 0 and not stdout:
                 raise RuntimeError(f"命令执行失败: {stderr}")

            # 5. 解析与入库
            parser_class = PARSERS.get(parser_type)
            if not parser_class:
                raise ValueError(f"未知解析器: {parser_type}")
            
            parser = parser_class()
            results_count = 0
            
            # --- 核心数据处理分支 ---
            
            # A. 子域名发现 (Subfinder) - [被动扫描阶段]
            #    Subfinder 默认查询被动源，不直接发包给目标，非常适合前期侦察
            if agent_type == "subdomain":
                async for res in parser.parse(stdout, data_mapping):
                    hostname = res.get("hostname")
                    if hostname:
                        # 检查是否存在
                        existing = await db.execute(select(models.Host).where(models.Host.hostname == hostname))
                        if not existing.scalars().first():
                            new_host = models.Host(
                                hostname=hostname,
                                organization_id=asset.organization_id,
                                root_asset_id=asset.id,
                                status="discovered"
                            )
                            db.add(new_host)
                            results_count += 1

            # B. 端口扫描 (Nmap) - [主动扫描阶段]
            #    Nmap 会直接向目标 IP 发送 TCP SYN 包，属于主动交互
            elif agent_type == "portscan":
                async for res in parser.parse(stdout, data_mapping):
                    ip = res.get("ip")
                    port_num = res.get("port")
                    service = res.get("service")
                    
                    if ip and port_num:
                        # 1. 确保 IP 存在 (如果不存在则创建)
                        existing_ip = await db.execute(select(models.IPAddress).where(models.IPAddress.ip_address == ip))
                        db_ip = existing_ip.scalars().first()
                        
                        if not db_ip:
                            db_ip = models.IPAddress(ip_address=ip, status="discovered")
                            db.add(db_ip)
                            await db.flush() # 立即获取 ID
                        
                        # 2. 存入端口 (去重)
                        existing_port = await db.execute(
                            select(models.Port).where(
                                models.Port.ip_address_id == db_ip.id,
                                models.Port.port_number == port_num
                            )
                        )
                        if not existing_port.scalars().first():
                            new_port = models.Port(
                                ip_address_id=db_ip.id,
                                port_number=port_num,
                                service_name=service
                            )
                            db.add(new_port)
                            results_count += 1

            # C. Web 服务探测 (httpx) - [主动扫描阶段]
            #    httpx 发送 HTTP 请求来获取 Title 和 Tech 指纹，是 Web 安全的核心步骤
            elif agent_type == "http":
                async for res in parser.parse(stdout, data_mapping):
                    url = res.get("url")
                    ip = res.get("ip")
                    port_val = res.get("port")
                    
                    if url:
                        # 兜底逻辑：如果 httpx 没返回 IP/Port，尝试从 URL 解析
                        # e.g., http://1.2.3.4:8080/
                        if not ip or not port_val:
                            parsed = urlparse(url)
                            # 如果 netloc 是 IP，直接用；如果是域名，这里没法直接解析，需要依赖 host 字段
                            # 为了简化，假设 httpx 配置了 -ip 选项
                            if not port_val:
                                port_val = parsed.port if parsed.port else (443 if parsed.scheme == 'https' else 80)

                        # 1. 查找或创建 IP (如果能拿到 IP)
                        db_ip_id = None
                        if ip:
                            existing_ip = await db.execute(select(models.IPAddress).where(models.IPAddress.ip_address == ip))
                            db_ip = existing_ip.scalars().first()
                            if not db_ip:
                                db_ip = models.IPAddress(ip_address=ip, status="discovered")
                                db.add(db_ip)
                                await db.flush()
                            db_ip_id = db_ip.id

                        # 2. 查找或创建 Port (如果有关联 IP)
                        db_port_id = None
                        if db_ip_id and port_val:
                            try:
                                port_num = int(port_val)
                            except:
                                port_num = 80

                            existing_port = await db.execute(
                                select(models.Port).where(
                                    models.Port.ip_address_id == db_ip_id, 
                                    models.Port.port_number == port_num
                                )
                            )
                            db_port = existing_port.scalars().first()
                            if not db_port:
                                db_port = models.Port(ip_address_id=db_ip_id, port_number=port_num, service_name="http")
                                db.add(db_port)
                                await db.flush()
                            db_port_id = db_port.id

                        # 3. 创建 HTTPService
                        existing_svc = await db.execute(select(models.HTTPService).where(models.HTTPService.url == url))
                        if not existing_svc.scalars().first():
                            # 如果找不到 Port，暂时允许 port_id 为空 (需要在 model 允许 nullable)
                            # 或者，我们这里强行要求 httpx 必须关联到一个 Port，否则不入库
                            if db_port_id: 
                                new_svc = models.HTTPService(
                                    port_id=db_port_id,
                                    url=url,
                                    title=res.get("title"),
                                    status_code=res.get("status_code"),
                                    tech=res.get("tech"),
                                    response_headers=res.get("web_server")
                                )
                                db.add(new_svc)
                                results_count += 1

            # D. 漏洞扫描 (Nuclei) - [主动扫描阶段]
            #    Nuclei 发送 Payload 验证漏洞，是攻击性最强的步骤
            elif agent_type == "vulnerability":
                async for res in parser.parse(stdout, data_mapping):
                    vuln_name = res.get("vulnerability_name")
                    severity = res.get("severity")
                    matched_url = res.get("url")
                    
                    if vuln_name:
                        # 存入 Vulnerability 表
                        # 这里未来可以做更细的关联：通过 matched_url 反查 HTTPService ID
                        new_vuln = models.Vulnerability(
                            vulnerability_name=vuln_name,
                            severity=severity or "medium",
                            matched_at=matched_url,
                            template_id=res.get("template_id"),
                            details=res 
                        )
                        db.add(new_vuln)
                        results_count += 1

            # --- 结束分支 ---

            if results_count > 0:
                await db.commit()
            
            task.status = "completed"
            task.completed_at = datetime.now(timezone.utc)
            task.log = f"扫描完成，新增 {results_count} 条数据。"
            await db.commit()
            print(f"[任务 {task_id}] 完成。新增数据: {results_count}")

        except Exception as e:
            print(f"[任务 {task_id}] 异常: {e}")
            await db.rollback()
            # 重新获取 task 以避免 Session 状态问题
            async with AsyncSessionLocal() as error_db:
                task_fail = await error_db.get(models.ScanTask, task_id)
                if task_fail:
                    task_fail.status = "failed"
                    task_fail.log = str(e)
                    await error_db.commit()