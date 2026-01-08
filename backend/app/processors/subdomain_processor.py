from sqlalchemy.future import select
from sqlalchemy import update
from app.data import models
from .base_processor import BaseProcessor
import datetime

class SubdomainProcessor(BaseProcessor):
    """
    处理被动子域名发现结果 (如 Subfinder)。
    逻辑：Host入库 -> IP入库 -> 建立DNS关联
    """
    async def process(self, res: dict) -> int:
        # 1. 提取基础字段
        hostname_raw = res.get("hostname") or res.get("host") or res.get("target")
        if not hostname_raw:
            return 0
            
        hostname = hostname_raw.lower().rstrip(".")
        record_type = res.get("record_type") or res.get("type") or "A"
        
        # 处理 IP 列表
        ip_values = set()
        ip_single = res.get("ip")
        if ip_single:
            if isinstance(ip_single, list):
                ip_values.update([ip for ip in ip_single if ip])
            else:
                ip_values.add(ip_single)
        
        ips_raw = res.get("ips")
        if isinstance(ips_raw, list):
            ip_values.update([ip for ip in ips_raw if ip])

        count_new = 0

        # ==========================================================
        # 2. Host 入库 (核心修复: 存在则更新归属)
        # ==========================================================
        stmt = select(models.Host).where(models.Host.hostname == hostname)
        existing = await self.db.execute(stmt)
        host_obj = existing.scalars().first()
        
        if not host_obj:
            # 不存在：创建新记录
            host_obj = models.Host(
                hostname=hostname,
                project_id=self.project_id,
                root_asset_id=self.root_asset_id,
                status="discovered",
                created_at=datetime.datetime.utcnow()
            )
            self.db.add(host_obj)
            await self.db.flush() # 获取 ID
            count_new += 1
        else:
            # [修复] 已存在：更新 root_asset_id 和 project_id，确保当前资产能看到它
            # 注意：这会将子域名“移动”到当前最新扫描的资产下
            if host_obj.root_asset_id != self.root_asset_id:
                host_obj.root_asset_id = self.root_asset_id
                host_obj.project_id = self.project_id
                # 可选：更新状态或时间
                # host_obj.updated_at = datetime.datetime.utcnow()
                self.db.add(host_obj)
                # 虽然不是"新增"，但这是"更新关联"，对用户来说数据出现了
                # 我们这里不加 count_new，因为从数据库角度它不是新行，但 UI 会有了

        # 3. IP 入库与 DNS 关联
        for ip_val in ip_values:
            # 查/存 IP
            stmt_ip = select(models.IPAddress).where(models.IPAddress.ip_address == ip_val)
            existing_ip = await self.db.execute(stmt_ip)
            ip_obj = existing_ip.scalars().first()
            
            if not ip_obj:
                ip_obj = models.IPAddress(
                    ip_address=ip_val,
                    project_id=self.project_id,
                    root_asset_id=self.root_asset_id,
                    status="discovered"
                )
                self.db.add(ip_obj)
                await self.db.flush()
                count_new += 1
            else:
                # 同样，如果 IP 存在，也更新归属（可选，视需求而定）
                if ip_obj.root_asset_id != self.root_asset_id:
                    ip_obj.root_asset_id = self.root_asset_id
                    self.db.add(ip_obj)

            # 建立 DNS 关联 (Host <-> IP)
            stmt_dns = select(models.DNSRecord).where(
                models.DNSRecord.host_id == host_obj.id,
                models.DNSRecord.ip_address_id == ip_obj.id,
                models.DNSRecord.record_type == record_type
            )
            existing_dns = await self.db.execute(stmt_dns)
            if not existing_dns.scalars().first():
                dns = models.DNSRecord(
                    host_id=host_obj.id,
                    ip_address_id=ip_obj.id,
                    record_type=record_type
                )
                self.db.add(dns)
                count_new += 1
                
        return count_new