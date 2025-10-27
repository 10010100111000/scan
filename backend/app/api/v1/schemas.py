# backend/app/api/v1/schemas.py
"""
定义 Pydantic 模型 (Schemas), 用于 API 的数据验证和响应。
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any, Dict

# --- 通用枚举 (简化表示, 实际应用中可使用 Python Enum) ---
AssetTypeEnum = "domain | cidr"
IPStatusEnum = "discovered | confirmed | archived"
HostStatusEnum = "discovered | confirmed | archived | out_of_scope"
SeverityEnum = "critical | high | medium | low | info"
VulnStatusEnum = "new | reviewed | false_positive | remediated"
FindingStatusEnum = "new | reviewed"
TaskStatusEnum = "pending | running | completed | failed"
WebFindingStatusEnum = "new | reviewed | false_positive"


# --- Tag Schemas ---
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class TagRead(TagBase):
    id: int
    # color: Optional[str] = None # 可选

    class Config:
        orm_mode = True

# --- Organization Schemas ---

class OrgBase(BaseModel):
    name: str

class OrgCreate(OrgBase):
    pass

class OrgRead(OrgBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# --- Asset Schemas ---

class AssetBase(BaseModel):
    name: str
    type: str # 实际应使用 AssetTypeEnum 或 Pydantic 的 Literal/Enum

class AssetCreate(AssetBase):
    # 创建时不需要 organization_id, 因为它从 URL 路径获取
    pass

class AssetRead(AssetBase):
    id: int
    organization_id: int
    created_at: datetime

    class Config:
        orm_mode = True

# --- IPAddress Schemas ---

class IPAddressBase(BaseModel):
    ip_address: str
    geolocation: Optional[Dict[str, Any]] = None
    vendor: Optional[str] = None
    asn_number: Optional[int] = None # 新增
    asn_name: Optional[str] = None # 新增
    asn_country: Optional[str] = None # 新增
    status: str = "discovered" # 实际应使用 IPStatusEnum
    is_bookmarked: bool = False

class IPAddressCreate(IPAddressBase):
    # IP 通常由扫描发现, API 创建可能用于手动添加
    pass

class IPAddressRead(IPAddressBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[TagRead] = [] # 包含关联的标签

    class Config:
        orm_mode = True

# --- Host Schemas ---

class HostBase(BaseModel):
    hostname: str
    status: str = "discovered" # 实际应使用 HostStatusEnum
    is_bookmarked: bool = False

class HostCreate(HostBase):
    # 创建时需要组织 ID, 根资产 ID 可选
    organization_id: int
    root_asset_id: Optional[int] = None

class HostRead(HostBase):
    id: int
    organization_id: int
    root_asset_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[TagRead] = [] # 包含关联的标签

    class Config:
        orm_mode = True

# --- Port Schemas ---
class PortBase(BaseModel):
    port_number: int
    service_name: Optional[str] = None

class PortCreate(PortBase):
     # 创建时需要 IP ID
     ip_address_id: int

class PortRead(PortBase):
    id: int
    ip_address_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# --- HTTPService Schemas ---
class HTTPServiceBase(BaseModel):
    url: str
    title: Optional[str] = None
    status_code: Optional[int] = None
    tech: Optional[Dict[str, Any]] = None
    response_headers: Optional[Dict[str, Any]] = None
    screenshot_path: Optional[str] = None
    is_bookmarked: bool = False
    favicon_hash: Optional[str] = None # 新增
    ssl_info: Optional[Dict[str, Any]] = None # 新增

class HTTPServiceCreate(HTTPServiceBase):
    # 创建时需要端口 ID
    port_id: int

class HTTPServiceRead(HTTPServiceBase):
    id: int
    port_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# --- Vulnerability Schemas ---
class VulnerabilityBase(BaseModel):
    vulnerability_name: str
    template_id: Optional[str] = None
    severity: str # 实际应使用 SeverityEnum
    matched_at: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    status: str = "new" # 实际应使用 VulnStatusEnum
    is_bookmarked: bool = False

class VulnerabilityCreate(VulnerabilityBase):
    # 创建时需要关联资产 ID (Host 或 HTTPService)
    host_id: Optional[int] = None
    http_service_id: Optional[int] = None
    # 应至少提供一个关联

class VulnerabilityRead(VulnerabilityBase):
    id: int
    host_id: Optional[int] = None
    http_service_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# --- GenericFinding Schemas ---
class GenericFindingBase(BaseModel):
    finding_type: str
    value: str
    details: Optional[Dict[str, Any]] = None
    status: str = "new" # 实际应使用 FindingStatusEnum
    related_asset_type: Optional[str] = None
    related_asset_id: Optional[int] = None

class GenericFindingCreate(GenericFindingBase):
    organization_id: int

class GenericFindingRead(GenericFindingBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# --- ScanTask Schemas ---
class ScanTaskBase(BaseModel):
    config_name: str
    asset_id: Optional[int] = None
    # target_type: Optional[str] = None # 未来可扩展
    # target_id: Optional[int] = None # 未来可扩展
    status: str = "pending" # 实际应使用 TaskStatusEnum

class ScanTaskCreate(ScanTaskBase):
    # 通常由系统内部根据 Asset ID 和 Config Name 创建
    pass

class ScanTaskRead(ScanTaskBase):
    id: int
    log: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# --- RawScanResult Schemas ---
class RawScanResultBase(BaseModel):
    data: Dict[str, Any]

class RawScanResultCreate(RawScanResultBase):
    scan_task_id: int

class RawScanResultRead(RawScanResultBase):
    id: int
    scan_task_id: int

    class Config:
        orm_mode = True

# --- WebFinding Schemas ---
class WebFindingBase(BaseModel):
    path: str
    status_code: Optional[int] = None
    content_length: Optional[int] = None
    status: str = "new" # 实际应使用 WebFindingStatusEnum

class WebFindingCreate(WebFindingBase):
    http_service_id: int

class WebFindingRead(WebFindingBase):
    id: int
    http_service_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# --- User Schemas ---

class AdminCreate(BaseModel):
    username: str
    password: str

class UserRead(BaseModel):
    id: int
    username: str
    is_active: bool

    class Config:
        orm_mode = True

# --- Token (认证) Schemas ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None