# backend/app/api/v1/schemas.py
"""
定义 Pydantic 模型 (Schemas), 用于 API 的数据验证和响应。
(增强版：添加了 Field 的 description 和 example)
"""
from pydantic import BaseModel, Field, ConfigDict # <-- 导入 Field
from datetime import datetime
from typing import Optional, List, Any, Dict, Literal

# --- 通用配置与枚举 ---
class OrmModel(BaseModel):
    """统一开启 from_attributes 以兼容 ORM 对象"""
    model_config = ConfigDict(from_attributes=True)

# --- 通用枚举 ---
AssetTypeLiteral = Literal["domain", "cidr"]
IPStatusLiteral = Literal["discovered", "confirmed", "archived"]
HostStatusLiteral = Literal["discovered", "confirmed", "archived", "out_of_scope"]
SeverityLiteral = Literal["critical", "high", "medium", "low", "info"]
VulnStatusLiteral = Literal["new", "reviewed", "false_positive", "remediated"]
FindingStatusLiteral = Literal["new", "reviewed"]
TaskStatusLiteral = Literal["pending", "running", "completed", "failed"]
WebFindingStatusLiteral = Literal["new", "reviewed", "false_positive"]


# --- Tag Schemas ---
class TagBase(BaseModel):
    name: str = Field(..., description="标签名称", example="敏感")

class TagCreate(TagBase):
    pass

class TagRead(TagBase, OrmModel):
    id: int

# --- Organization Schemas ---

class OrgBase(BaseModel):
    name: str = Field(..., description="组织或项目的名称", example="我的测试项目")

class OrgCreate(OrgBase):
    pass

class OrgRead(OrgBase, OrmModel):
    id: int
    created_at: datetime

# --- Asset Schemas ---

class AssetBase(BaseModel):
    name: str = Field(..., description="根资产的名称", example="example.com")
    type: AssetTypeLiteral = Field(..., description="根资产的类型", example="domain")

class AssetCreate(AssetBase):
    # 创建时不需要 organization_id, 因为它从 URL 路径获取
    # 我们可以在这里添加一个示例, FastAPI 会在 /docs 的 Request Body 中显示它
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "example.com",
                "type": "domain"
            }
        }
    )

class AssetRead(AssetBase, OrmModel):
    id: int
    organization_id: int
    created_at: datetime

# --- IPAddress Schemas ---

class IPAddressBase(BaseModel):
    ip_address: str = Field(..., description="IP 地址", example="192.168.1.1")
    geolocation: Optional[Dict[str, Any]] = Field(None, description="地理位置信息 (JSON)")
    vendor: Optional[str] = Field(None, description="IP 归属厂商", example="Aliyun")
    asn_number: Optional[int] = Field(None, description="ASN 编号", example=12345)
    asn_name: Optional[str] = Field(None, description="ASN 名称", example="EXAMPLE-ASN")
    asn_country: Optional[str] = Field(None, description="ASN 国家", example="US")
    status: IPStatusLiteral = Field("discovered", description="IP 状态")
    is_bookmarked: bool = Field(False, description="是否收藏")

class IPAddressCreate(IPAddressBase):
    pass

class IPAddressRead(IPAddressBase, OrmModel):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[TagRead] = []

# --- Host Schemas ---

class HostBase(BaseModel):
    hostname: str = Field(..., description="主机名或子域名", example="app.example.com")
    status: HostStatusLiteral = Field("discovered", description="主机状态")
    is_bookmarked: bool = Field(False, description="是否收藏")

class HostCreate(HostBase):
    organization_id: int = Field(..., description="所属组织的 ID")
    root_asset_id: Optional[int] = Field(None, description="关联的根资产 ID (可选)")

class HostRead(HostBase, OrmModel):
    id: int
    organization_id: int
    root_asset_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[TagRead] = []


# --- Port Schemas ---
class PortBase(BaseModel):
    port_number: int = Field(..., description="端口号", example=443)
    service_name: Optional[str] = Field(None, description="服务名称 (由扫描器识别)", example="https")

class PortCreate(PortBase):
     ip_address_id: int

class PortRead(PortBase, OrmModel):
    id: int
    ip_address_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

# --- HTTPService Schemas ---
class HTTPServiceBase(BaseModel):
    url: str = Field(..., description="完整的 URL", example="https://app.example.com")
    title: Optional[str] = Field(None, description="网页标题")
    status_code: Optional[int] = Field(None, description="HTTP 状态码", example=200)
    tech: Optional[Dict[str, Any]] = Field(None, description="识别出的技术栈 (JSON)")
    response_headers: Optional[Dict[str, Any]] = Field(None, description="HTTP 响应头 (JSON)")
    screenshot_path: Optional[str] = Field(None, description="截图文件路径 (服务器本地路径)")
    is_bookmarked: bool = Field(False, description="是否收藏")
    favicon_hash: Optional[str] = Field(None, description="Favicon 的 MurmurHash3 哈希值")
    ssl_info: Optional[Dict[str, Any]] = Field(None, description="SSL/TLS 证书信息 (JSON)")

class HTTPServiceCreate(HTTPServiceBase):
    port_id: int

class HTTPServiceRead(HTTPServiceBase, OrmModel):
    id: int
    port_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

# --- Vulnerability Schemas ---
class VulnerabilityBase(BaseModel):
    vulnerability_name: str = Field(..., description="漏洞名称或 CVE ID", example="CVE-2024-1234")
    template_id: Optional[str] = Field(None, description="Nuclei 模板 ID (如果适用)")
    severity: SeverityLiteral = Field(..., description="漏洞严重程度")
    matched_at: Optional[str] = Field(None, description="漏洞触发的具体位置 (URL, 参数等)")
    details: Optional[Dict[str, Any]] = Field(None, description="漏洞详情 (JSON, 例如 Nuclei 的输出)")
    status: VulnStatusLiteral = Field("new", description="漏洞状态")
    is_bookmarked: bool = Field(False, description="是否收藏")

class VulnerabilityCreate(VulnerabilityBase):
    host_id: Optional[int] = None
    http_service_id: Optional[int] = None

class VulnerabilityRead(VulnerabilityBase, OrmModel):
    id: int
    host_id: Optional[int] = None
    http_service_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# --- Summaries for list endpoints ---
class PortSummary(BaseModel):
    id: int = Field(..., description="端口 ID")
    ip: str = Field(..., description="IP 地址")
    port: int = Field(..., description="端口号")
    service: Optional[str] = Field(None, description="服务名称")


class HTTPServiceSummary(BaseModel):
    id: int = Field(..., description="HTTP 服务 ID")
    url: str = Field(..., description="完整 URL")
    title: Optional[str] = Field(None, description="页面标题")
    tech: Optional[Dict[str, Any]] = Field(None, description="技术栈指纹")
    status: Optional[int] = Field(None, description="HTTP 状态码")


class VulnerabilitySummary(BaseModel):
    id: int = Field(..., description="漏洞 ID")
    name: str = Field(..., description="漏洞名称或模板名")
    severity: SeverityLiteral = Field(..., description="漏洞严重程度")
    url: Optional[str] = Field(None, description="命中的 URL")


# --- Summaries for list endpoints ---
class PortSummary(BaseModel):
    id: int = Field(..., description="端口 ID")
    ip: str = Field(..., description="IP 地址")
    port: int = Field(..., description="端口号")
    service: Optional[str] = Field(None, description="服务名称")


class HTTPServiceSummary(BaseModel):
    id: int = Field(..., description="HTTP 服务 ID")
    url: str = Field(..., description="完整 URL")
    title: Optional[str] = Field(None, description="页面标题")
    tech: Optional[Dict[str, Any]] = Field(None, description="技术栈指纹")
    status: Optional[int] = Field(None, description="HTTP 状态码")


class VulnerabilitySummary(BaseModel):
    id: int = Field(..., description="漏洞 ID")
    name: str = Field(..., description="漏洞名称或模板名")
    severity: SeverityLiteral = Field(..., description="漏洞严重程度")
    url: Optional[str] = Field(None, description="命中的 URL")

# --- GenericFinding Schemas ---
class GenericFindingBase(BaseModel):
    finding_type: str = Field(..., description="发现物的类型", example="dns_cname")
    value: str = Field(..., description="发现物的值", example="app.cdn.provider.com")
    details: Optional[Dict[str, Any]] = Field(None, description="额外信息 (JSON)")
    status: FindingStatusLiteral = Field("new", description="发现物状态")
    related_asset_type: Optional[str] = Field(None, description="关联资产类型 (host, ip_address)")
    related_asset_id: Optional[int] = Field(None, description="关联资产 ID")

class GenericFindingCreate(GenericFindingBase):
    organization_id: int

class GenericFindingRead(GenericFindingBase, OrmModel):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

# --- ScanTask Schemas ---
class ScanTaskBase(BaseModel):
    config_name: str = Field(..., description="使用的扫描配置名称 (来自 scanners.yaml)", example="Subfinder (默认)")
    asset_id: Optional[int] = Field(None, description="关联的根资产 ID (可选)")
    status: TaskStatusLiteral = Field("pending", description="任务状态")

class ScanTaskCreate(ScanTaskBase):
    # 通常由 /assets/{asset_id}/scan 接口内部创建
    pass

class ScanTaskRead(ScanTaskBase, OrmModel):
    id: int
    log: Optional[str] = Field(None, description="任务执行日志 (通常只在失败时填充)")
    created_at: datetime
    completed_at: Optional[datetime] = None


class ScanConfigSummary(BaseModel):
    name: str = Field(..., description="扫描配置名称")
    agent_type: Optional[str] = Field(None, description="扫描代理类型（subdomain/portscan/http/vulnerability 等）")
    description: Optional[str] = Field(None, description="配置描述")


class ScanConfigSummary(BaseModel):
    name: str = Field(..., description="扫描配置名称")
    agent_type: Optional[str] = Field(None, description="扫描代理类型（subdomain/portscan/http/vulnerability 等）")
    description: Optional[str] = Field(None, description="配置描述")

# --- RawScanResult Schemas ---
class RawScanResultBase(BaseModel):
    data: Dict[str, Any] = Field(..., description="扫描工具输出的单条原始数据 (JSON)")

class RawScanResultCreate(RawScanResultBase):
    scan_task_id: int

class RawScanResultRead(RawScanResultBase, OrmModel):
    id: int
    scan_task_id: int

# --- WebFinding Schemas ---
class WebFindingBase(BaseModel):
    path: str = Field(..., description="发现的 Web 路径", example="/admin.php")
    status_code: Optional[int] = Field(None, description="HTTP 状态码")
    content_length: Optional[int] = Field(None, description="响应内容长度")
    status: WebFindingStatusLiteral = Field("new", description="路径状态")

class WebFindingCreate(WebFindingBase):
    http_service_id: int

class WebFindingRead(WebFindingBase, OrmModel):
    id: int
    http_service_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# --- User Schemas ---

class AdminCreate(BaseModel):
    username: str = Field(..., description="管理员用户名")
    password: str = Field(..., description="管理员密码")
    email: Optional[str] = Field(None, description="管理员邮箱（可选）")

class UserRead(OrmModel):
    id: int
    username: str
    is_active: bool

# --- Token (认证) Schemas ---

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
