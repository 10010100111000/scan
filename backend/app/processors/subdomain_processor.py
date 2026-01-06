from sqlalchemy.future import select
from app.data import models
from .base_processor import BaseProcessor

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
        
        # 处理 IP 列表 (Subfinder 可能返回 ip 字符串或 ips 列表)
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

        # 2. Host 入库 (去重)
        stmt = select(models.Host).where(models.Host.hostname == hostname)
        existing = await self.db.execute(stmt)
        host_obj = existing.scalars().first()
        
        if not host_obj:
            host_obj = models.Host(
                hostname=hostname,
                project_id=self.project_id,
                root_asset_id=self.root_asset_id,
                status="discovered"
            )
            self.db.add(host_obj)
            await self.db.flush() # 立即获取 ID
            count_new += 1

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