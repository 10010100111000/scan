# backend/app/api/v1/schemas.py
"""
定义 Pydantic 模型 (Schemas), 用于 API 的数据验证和响应。
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any, Dict

# --- 通用枚举 (与 models.py 保持一致) ---
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
    type: str # 对应 Enum("domain", "cidr")

class AssetCreate(AssetBase):
    organization_id: int

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
    status: str = "discovered" # 对应 Enum
    is_bookmarked: bool = False

class IPAddressCreate(IPAddressBase):
    pass

class IPAddressRead(IPAddressBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[TagRead] = [] # 包含 IP 的标签列表

    class Config:
        orm_mode = True

# --- Host Schemas ---

class HostBase(BaseModel):
    hostname: str
    status: str = "discovered" # 对应 Enum
    is_bookmarked: bool = False

class HostCreate(HostBase):
    organization_id: int
    root_asset_id: Optional[int] = None

class HostRead(HostBase):
    id: int
    organization_id: int
    root_asset_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    tags: List[TagRead] = [] # 包含 Host 的标签列表

    class Config:
        orm_mode = True

# --- Port Schemas ---
class PortBase(BaseModel):
    port_number: int
    service_name: Optional[str] = None

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
    # *** 新增：Favicon 哈希 ***
    favicon_hash: Optional[str] = None
    # *** 结束新增 ***
    ssl_info: Optional[Dict[str, Any]] = None # 证书信息

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
    severity: str # 对应 Enum
    matched_at: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    status: str = "new" # 对应 Enum
    is_bookmarked: bool = False

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
    status: str = "new" # 对应 Enum
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
    status: str = "pending" # 对应 Enum
    log: Optional[str] = None
    completed_at: Optional[datetime] = None

class ScanTaskCreate(ScanTaskBase):
    pass

class ScanTaskRead(ScanTaskBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# --- RawScanResult Schemas ---
class RawScanResultBase(BaseModel):
    data: Dict[str, Any]

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
    status: str = "new" # 对应 Enum

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