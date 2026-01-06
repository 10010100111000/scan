from app.data import models
from .base_processor import BaseProcessor

class VulnProcessor(BaseProcessor):
    """
    处理漏洞扫描结果 (Nuclei)。
    """
    async def process(self, res: dict) -> int:
        vuln_name = res.get("vulnerability_name")
        severity = res.get("severity")
        matched_url = res.get("url")
        
        if not vuln_name:
            return 0
            
        new_vuln = models.Vulnerability(
            vulnerability_name=vuln_name,
            severity=severity or "medium",
            matched_at=matched_url,
            template_id=res.get("template_id"),
            details=res,
            # 未来可扩展: 关联到 host_id 或 http_service_id
        )
        self.db.add(new_vuln)
        return 1