from urllib.parse import urlparse
from sqlalchemy.future import select
from app.data import models
from .base_processor import BaseProcessor

class HttpProcessor(BaseProcessor):
    """
    处理 Web 探测结果 (httpx)。
    逻辑：IP入库(含ASN更新) -> Port入库 -> HTTPService入库
    """
    async def process(self, res: dict) -> int:
        url = res.get("url")
        ip = res.get("ip")
        port_val = res.get("port")
        
        # [增强] 提取 ASN 字段 (httpx -asn -json 输出)
        # 假设 parser 已经展平了数据，或者我们手动从 res['asn'] 提取
        # httpx 标准 json 结构: "asn": {"as-number": "AS15169", ...}
        asn_data = res.get("asn", {})
        asn_number_str = asn_data.get("as-number") # e.g., "AS15169"
        asn_name = asn_data.get("as-name")
        asn_country = asn_data.get("as-country") or list(asn_data.get("as-country", []))
        if isinstance(asn_country, list) and asn_country:
             asn_country = asn_country[0]

        # 尝试清洗 AS 号码 (去掉 'AS' 前缀转为 int)
        asn_int = None
        if asn_number_str and str(asn_number_str).upper().startswith("AS"):
            try:
                asn_int = int(str(asn_number_str)[2:])
            except:
                pass
        
        if not url:
            return 0
            
        # 兜底：从 URL 解析 IP/Port
        if not ip or not port_val:
            parsed = urlparse(url)
            if not port_val:
                port_val = parsed.port if parsed.port else (443 if parsed.scheme == 'https' else 80)
        
        count_new = 0
        db_ip_id = None

        # 1. IP 处理 (关键：更新 ASN 信息)
        if ip:
            stmt_ip = select(models.IPAddress).where(models.IPAddress.ip_address == ip)
            existing_ip = await self.db.execute(stmt_ip)
            db_ip = existing_ip.scalars().first()
            
            if not db_ip:
                db_ip = models.IPAddress(
                    ip_address=ip,
                    project_id=self.project_id,
                    root_asset_id=self.root_asset_id,
                    status="discovered"
                )
                self.db.add(db_ip)
                await self.db.flush()
            
            # [更新] 如果发现新的 ASN 信息，则更新现有记录
            is_dirty = False
            if asn_int and db_ip.asn_number != asn_int:
                db_ip.asn_number = asn_int
                is_dirty = True
            if asn_name and db_ip.asn_name != asn_name:
                db_ip.asn_name = asn_name
                is_dirty = True
            if asn_country and db_ip.asn_country != asn_country:
                db_ip.asn_country = asn_country
                is_dirty = True
            
            if is_dirty:
                self.db.add(db_ip) # 标记更新

            db_ip_id = db_ip.id

        # 2. Port 处理
        db_port_id = None
        if db_ip_id and port_val:
            try:
                port_num = int(port_val)
            except:
                port_num = 80
            
            stmt_port = select(models.Port).where(
                models.Port.ip_address_id == db_ip_id,
                models.Port.port_number == port_num
            )
            existing_port = await self.db.execute(stmt_port)
            db_port = existing_port.scalars().first()
            
            if not db_port:
                db_port = models.Port(
                    ip_address_id=db_ip_id, 
                    port_number=port_num, 
                    service_name="http"
                )
                self.db.add(db_port)
                await self.db.flush()
            db_port_id = db_port.id

        # 3. HTTP Service 处理
        stmt_svc = select(models.HTTPService).where(models.HTTPService.url == url)
        existing_svc = await self.db.execute(stmt_svc)
        
        if not existing_svc.scalars().first():
            # 只有当关联到具体 Port 时才存服务，保证数据结构完整
            if db_port_id:
                new_svc = models.HTTPService(
                    port_id=db_port_id,
                    url=url,
                    title=res.get("title"),
                    status_code=res.get("status_code"),
                    tech=res.get("tech"),
                    response_headers=res.get("web_server"),
                    favicon_hash=res.get("favicon_hash"),
                    ssl_info=res.get("ssl_info")
                )
                self.db.add(new_svc)
                count_new += 1
                
        return count_new