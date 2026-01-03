# backend/app/data/models.py
"""
定义数据库的所有表模型 (最终版本，包含完整的标签支持 + Favicon Hash + ASN信息)
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, func, Boolean, ForeignKey, Text, JSON, Enum, Table, UniqueConstraint
)
from sqlalchemy.orm import relationship # 用于定义表之间的关系

# 导入Base类，它是所有模型的基类
from .base import Base

# --- 多对多关联表 (Association Tables) ---

# Host 和 Tag 之间的关联表
host_tags_association = Table(
    "host_tags",
    Base.metadata,
    Column("host_id", Integer, ForeignKey("hosts.id", ondelete="CASCADE"), primary_key=True), # 级联删除
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True), # 级联删除
)

# IPAddress 和 Tag 之间的关联表
ipaddress_tags_association = Table(
    "ipaddress_tags",
    Base.metadata,
    Column("ipaddress_id", Integer, ForeignKey("ip_addresses.id", ondelete="CASCADE"), primary_key=True), # 级联删除
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True), # 级联删除
)

# --- 核心资产模型 (80/20 混合模型) ---

class Project(Base):
    """项目"""
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # --- 关系 ---
    assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")
    hosts = relationship("Host", back_populates="project", cascade="all, delete-orphan")
    ip_addresses = relationship("IPAddress", back_populates="project", cascade="all, delete-orphan")
    generic_findings = relationship("GenericFinding", back_populates="project", cascade="all, delete-orphan")


class Asset(Base):
    """根资产 (用户输入的初始目标)"""
    __tablename__ = "assets"
    __table_args__ = (
        # 同一项目下的资产名称保持唯一，避免重复扫描和数据污染
        UniqueConstraint("project_id", "name", name="uq_asset_project_name"),
    )
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False, index=True) # e.g., "example.com" or "1.2.3.0/24"
    type = Column(Enum("domain", "cidr", name="asset_type_enum"), nullable=False) # 枚举类型
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # --- 关系 ---
    project = relationship("Project", back_populates="assets")
    hosts = relationship("Host", back_populates="root_asset", cascade="all, delete-orphan")
    ip_addresses = relationship("IPAddress", back_populates="root_asset", cascade="all, delete-orphan")
    scan_tasks = relationship("ScanTask", back_populates="asset", cascade="all, delete-orphan")


class Tag(Base):
    """标签"""
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    # (可选) 定义反向关系
    # hosts = relationship("Host", secondary=host_tags_association, back_populates="tags")
    # ip_addresses = relationship("IPAddress", secondary=ipaddress_tags_association, back_populates="tags")


class IPAddress(Base):
    """IP 地址资产 (我们的核心)"""
    __tablename__ = "ip_addresses"
    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String, unique=True, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    root_asset_id = Column(Integer, ForeignKey("assets.id", ondelete="SET NULL"), nullable=True, index=True)
    geolocation = Column(JSON, nullable=True)
    vendor = Column(String, nullable=True)
    # --- 新增 ASN 字段 ---
    asn_number = Column(Integer, nullable=True, index=True)
    asn_name = Column(String, nullable=True)
    asn_country = Column(String, nullable=True, index=True)
    # --- 结束新增 ---
    status = Column(Enum("discovered", "confirmed", "archived", name="ip_status_enum"), default="discovered", nullable=False, index=True)
    is_bookmarked = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- 关系 ---
    ports = relationship("Port", back_populates="ip_address", cascade="all, delete-orphan")
    hosts = relationship("Host", secondary="dns_records", back_populates="ip_addresses") # 多对多
    tags = relationship("Tag", secondary=ipaddress_tags_association) # IP 的标签关系
    project = relationship("Project", back_populates="ip_addresses")
    root_asset = relationship("Asset", back_populates="ip_addresses")


class Host(Base):
    """主机名/域名资产"""
    __tablename__ = "hosts"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False) # 归属
    root_asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True) # 从哪个根资产发现的
    hostname = Column(String, unique=True, nullable=False, index=True)
    status = Column(Enum("discovered", "confirmed", "archived", "out_of_scope", name="host_status_enum"), default="discovered", nullable=False, index=True)
    is_bookmarked = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- 关系 ---
    project = relationship("Project", back_populates="hosts")
    root_asset = relationship("Asset", back_populates="hosts")
    ip_addresses = relationship("IPAddress", secondary="dns_records", back_populates="hosts") # 多对多
    vulnerabilities = relationship("Vulnerability", back_populates="host", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary=host_tags_association) # Host 的标签关系


class DNSRecord(Base):
    """DNS 记录 (多对多关联表)"""
    __tablename__ = "dns_records"
    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False) # 级联删除
    ip_address_id = Column(Integer, ForeignKey("ip_addresses.id", ondelete="CASCADE"), nullable=False) # 级联删除
    record_type = Column(String, nullable=True) # e.g., "A", "CNAME"
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), onupdate=func.now())


class Port(Base):
    """端口"""
    __tablename__ = "ports"
    id = Column(Integer, primary_key=True, index=True)
    ip_address_id = Column(Integer, ForeignKey("ip_addresses.id", ondelete="CASCADE"), nullable=False) # 级联删除
    port_number = Column(Integer, nullable=False, index=True)
    service_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- 关系 ---
    ip_address = relationship("IPAddress", back_populates="ports")
    http_services = relationship("HTTPService", back_populates="port", cascade="all, delete-orphan")


class HTTPService(Base):
    """Web 服务"""
    __tablename__ = "http_services"
    id = Column(Integer, primary_key=True, index=True)
    port_id = Column(Integer, ForeignKey("ports.id", ondelete="CASCADE"), nullable=False) # 级联删除
    url = Column(String, nullable=False, index=True)
    title = Column(String, nullable=True)
    status_code = Column(Integer, nullable=True, index=True)
    tech = Column(JSON, nullable=True)
    response_headers = Column(JSON, nullable=True)
    screenshot_path = Column(String, nullable=True)
    is_bookmarked = Column(Boolean, default=False, nullable=False, index=True)
    favicon_hash = Column(String, nullable=True, index=True) # Favicon 哈希
    ssl_info = Column(JSON, nullable=True) # 证书信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- 关系 ---
    port = relationship("Port", back_populates="http_services")
    vulnerabilities = relationship("Vulnerability", back_populates="http_service", cascade="all, delete-orphan")
    web_findings = relationship("WebFinding", back_populates="http_service", cascade="all, delete-orphan")


class Vulnerability(Base):
    """漏洞"""
    __tablename__ = "vulnerabilities"
    id = Column(Integer, primary_key=True, index=True)
    host_id = Column(Integer, ForeignKey("hosts.id", ondelete="CASCADE"), nullable=True) # 级联删除
    http_service_id = Column(Integer, ForeignKey("http_services.id", ondelete="CASCADE"), nullable=True) # 级联删除

    vulnerability_name = Column(String, nullable=False, index=True)
    template_id = Column(String, nullable=True, index=True)
    severity = Column(Enum("critical", "high", "medium", "low", "info", name="severity_enum"), nullable=False, index=True)
    matched_at = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    status = Column(Enum("new", "reviewed", "false_positive", "remediated", name="vuln_status_enum"), default="new", nullable=False, index=True)
    is_bookmarked = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- 关系 ---
    host = relationship("Host", back_populates="vulnerabilities")
    http_service = relationship("HTTPService", back_populates="vulnerabilities")


class GenericFinding(Base):
    """通用发现物 (万能表, 用于扩展)"""
    __tablename__ = "generic_findings"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    related_asset_type = Column(String, nullable=True, index=True) # e.g., "host", "ip_address"
    related_asset_id = Column(Integer, nullable=True, index=True)

    finding_type = Column(String, nullable=False, index=True) # e.g., "dns_cname", "dns_mx", "s3_bucket", "api_key"
    value = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    status = Column(Enum("new", "reviewed", name="finding_status_enum"), default="new", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- 关系 ---
    project = relationship("Project", back_populates="generic_findings")


# --- 日志与 Triage 模型 ---

class ScanTask(Base):
    """扫描任务"""
    __tablename__ = "scan_tasks"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True) # 关联到根资产

    config_name = Column(String, nullable=False, index=True) # 使用的 scanners.yaml 中的配置名
    status = Column(Enum("pending", "running", "completed", "failed", name="task_status_enum"), default="pending", nullable=False, index=True)
    log = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # --- 关系 ---
    asset = relationship("Asset", back_populates="scan_tasks")
    raw_results = relationship("RawScanResult", back_populates="scan_task", cascade="all, delete-orphan")


class RawScanResult(Base):
    """原始扫描结果 (噪音隔离库)"""
    __tablename__ = "raw_scan_results"
    id = Column(Integer, primary_key=True, index=True)
    scan_task_id = Column(Integer, ForeignKey("scan_tasks.id", ondelete="CASCADE"), nullable=False) # 级联删除
    data = Column(JSON, nullable=False) # 统一存 JSON Lines 解析后的单条 JSON 数据

    # --- 关系 ---
    scan_task = relationship("ScanTask", back_populates="raw_results")


class WebFinding(Base):
    """Web 路径发现物 (从 RawScanResult 提升的精华)"""
    __tablename__ = "web_findings"
    id = Column(Integer, primary_key=True, index=True)
    http_service_id = Column(Integer, ForeignKey("http_services.id", ondelete="CASCADE"), nullable=False) # 级联删除
    path = Column(String, nullable=False, index=True)
    status_code = Column(Integer, nullable=True)
    content_length = Column(Integer, nullable=True)
    status = Column(Enum("new", "reviewed", "false_positive", name="webfinding_status_enum"), default="new", nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # --- 关系 ---
    http_service = relationship("HTTPService", back_populates="web_findings")


# --- 用户模型 (已存在) ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    # 新增 email 字段
    email = Column(String, unique=True, index=True, nullable=True) 
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    # 新增 is_superuser 字段
    is_superuser = Column(Boolean, default=False)
