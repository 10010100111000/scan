from sqlalchemy.future import select
from app.data import models
from .base_processor import BaseProcessor

class PortProcessor(BaseProcessor):
    """
    处理端口扫描结果 (如 Nmap/Naabu)。
    逻辑：IP入库 -> Port入库
    """
    async def process(self, res: dict) -> int:
        ip = res.get("ip")
        port_num = res.get("port")
        service = res.get("service")
        
        if not ip or not port_num:
            return 0
            
        count_new = 0
        
        # 1. IP 入库
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
        
        # 2. Port 入库
        stmt_port = select(models.Port).where(
            models.Port.ip_address_id == db_ip.id,
            models.Port.port_number == port_num
        )
        existing_port = await self.db.execute(stmt_port)
        if not existing_port.scalars().first():
            new_port = models.Port(
                ip_address_id=db_ip.id,
                port_number=port_num,
                service_name=service
            )
            self.db.add(new_port)
            count_new += 1
            
        return count_new