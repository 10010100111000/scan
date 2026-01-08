// frontend/src/api/scan.ts
import http, { request } from '@/api/http'

// ==========================================
// 1. 类型定义 (Types)
// ==========================================

export interface ScanStrategySummary {
  strategy_name: string
  description?: string | null
  steps: string[]
}

export interface Project {
  id: number
  name: string
  created_at: string
}

export interface Asset {
  id: number
  name: string
  type: 'domain' | 'cidr'
  project_id: number
  created_at: string
}

export interface AssetSearchResult extends Asset {
  project_name?: string | null
}

// 任务相关
export interface ScanTask {
  id: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  config_name: string
  asset_id: number | null
  project_id?: number | null
  project_name?: string | null
  created_at: string
  completed_at?: string | null
  log?: string | null
  strategy_name?: string | null
  strategy_steps?: string[] | null
  step_statuses?: ScanTaskStepStatus[] | null
  current_step?: string | null
}

export interface ScanTaskStepStatus {
  config_name: string
  task_id?: number | null
  status?: ScanTask['status'] | null
  completed_at?: string | null
  stage?: string | null
  artifact_path?: string | null
}

export interface ScanSubmissionResponse {
  strategy_name: string
  task_ids: number[]
}

export interface CreateScanRequest {
  asset_id: number
  strategy_name: string
}

export interface AssetQueryParams {
  skip?: number
  limit?: number
  search?: string
  project_id?: number
}

// --- 结果详情相关类型 (Results Types) ---

// [新增] 主机/子域名类型
export interface Host {
  id: number
  hostname: string
  status: string
  created_at: string
  ips: string[]
  is_bookmarked: boolean
  project_id: number
  root_asset_id: number
}

// 兼容旧命名，如果其他地方用到
export type HostSummary = Host

// [新增] 主机列表响应结构 (支持游标分页)
export interface HostListResponse {
  items: Host[]
  next_cursor: number | null
  has_more: boolean
  limit: number
}

// [新增] 端口类型
export interface Port {
  id: number
  ip: string
  port: number
  service?: string | null
  protocol?: string | null
  root_asset_id?: number | null
}

export type PortSummary = Port

// [新增] Web 服务类型
export interface WebService {
  id: number
  url: string
  title?: string | null
  tech?: any | null // 技术栈指纹
  status?: number | null
}

export type HTTPServiceSummary = WebService

// [新增] 漏洞类型
export interface Vulnerability {
  id: number
  name: string
  severity: string
  url?: string | null
  template_id?: string | null
  details?: Record<string, unknown> | null
  host_id?: number | null
  http_service_id?: number | null
  created_at?: string | null
  updated_at?: string | null
}

export type VulnerabilitySummary = Vulnerability

// [新增] 通用分页列表响应
export interface OffsetListResponse<T> {
  items: T[]
  next_offset: number | null
  has_more: boolean
  limit: number
}

// ==========================================
// 2. 核心 API 方法 (Core APIs)
// ==========================================

/**
 * [Assets - Global] 获取资产列表
 * 支持分页、搜索，以及可选的 project_id 过滤
 * 对应后端: GET /api/v1/assets
 */
export async function fetchAssets(params: AssetQueryParams = {}) {
  return request<Asset[]>(http.get('/assets', { params }))
}

/**
 * [Assets - Helper] 获取全局资产 (不带项目过滤)
 */
export async function fetchGlobalAssets(params: Omit<AssetQueryParams, 'project_id'> = {}) {
  return fetchAssets(params)
}

/**
 * [Assets - Helper] 获取指定项目的资产
 * 实质是调用 fetchAssets 并强制带上 project_id
 */
export async function fetchAssetsForProject(
  projectId: number, 
  params: Omit<AssetQueryParams, 'project_id'> = {}
) {
  return fetchAssets({ ...params, project_id: projectId })
}

/**
 * [Assets - Search] 全局精确查找资产 (用于去重/跳转)
 * 对应后端: GET /api/v1/assets/search
 */
export async function searchAssetsByName(name: string, limit = 10) {
  return request<AssetSearchResult[]>(http.get('/assets/search', { params: { name, limit } }))
}

/**
 * [Assets - Create] 创建新资产
 * 对应后端: POST /api/v1/assets
 */
export async function createAsset(projectId: number, payload: { name: string; type: 'domain' | 'cidr' }) {
  // 注意：后端现在要求 project_id 在 Body 中
  return request<Asset>(http.post('/assets', {
    ...payload,
    project_id: projectId
  }))
}

/**
 * [Assets - Delete] 删除资产
 * 对应后端: DELETE /api/v1/assets/{id}
 */
export async function deleteAsset(assetId: number) {
  return request<{ message?: string }>(http.delete(`/assets/${assetId}`))
}

/**
 * [Assets - Detail] 获取单个资产详情
 */
export async function fetchAssetById(assetId: number) {
  return request<Asset>(http.get(`/assets/${assetId}`))
}

/**
 * [Scans - Action] 触发扫描任务
 * 对应后端: POST /api/v1/scans
 */
export async function triggerScan(payload: CreateScanRequest) {
  return request<ScanSubmissionResponse>(http.post('/scans', payload))
}

/**
 * [Projects] 获取项目列表
 */
export async function fetchProjects(params: { skip?: number; limit?: number; search?: string } = {}) {
  return request<Project[]>(http.get('/projects', { params }))
}

/**
 * [Projects] 创建项目
 */
export async function createProject(payload: { name: string }) {
  return request<Project>(http.post('/projects', payload))
}

/**
 * [Strategies] 获取扫描策略
 */
export async function fetchScanStrategies() {
  return request<ScanStrategySummary[]>(http.get('/scan-strategies'))
}

// ==========================================
// 3. 任务与结果 API (Tasks & Results)
// ==========================================

export async function listTasks(params: Record<string, unknown> = {}) {
  return request<ScanTask[]>(http.get('/tasks', { params }))
}

export async function fetchTask(taskId: number) {
  return request<ScanTask>(http.get(`/tasks/${taskId}`))
}

export async function retryTask(taskId: number, payload: { mode: 'strategy' | 'step' }) {
  return request<ScanSubmissionResponse>(http.post(`/tasks/${taskId}/retry`, payload))
}

// --- 结果查询接口 (Host/Port/Web/Vuln) ---

/**
 * [Results] 获取资产下的子域名/主机
 * 注意：后端使用的是 Cursor 分页 (基于 ID)，而不是 skip/limit
 */
export async function fetchAssetHosts(
  assetId: number,
  params: { limit?: number; cursor?: number | null } = {}
) {
  return request<HostListResponse>(http.get(`/results/assets/${assetId}/hosts`, { params }))
}

/**
 * [Results] 获取资产下的开放端口
 */
export async function fetchAssetPorts(
  assetId: number,
  params: { skip?: number; limit?: number } = {}
) {
  return request<OffsetListResponse<Port>>(http.get(`/results/assets/${assetId}/ports`, { params }))
}

/**
 * [Results] 获取资产下的 Web 服务
 * 包含 Title, Tech指纹, Status Code 等丰富信息
 */
export async function fetchAssetWeb(
  assetId: number,
  params: { skip?: number; limit?: number } = {}
) {
  return request<OffsetListResponse<WebService>>(http.get(`/results/assets/${assetId}/web`, { params }))
}

/**
 * [Results] 获取资产下的漏洞信息
 */
export async function fetchAssetVulns(
  assetId: number,
  params: { skip?: number; limit?: number } = {}
) {
  return request<OffsetListResponse<Vulnerability>>(http.get(`/results/assets/${assetId}/vulns`, { params }))
}

// --- 单个详情查询 ---

export async function fetchHostDetail(hostId: number) {
  return request<Host>(http.get(`/results/hosts/${hostId}`))
}

export async function fetchPortDetail(portId: number) {
  return request<Port>(http.get(`/results/ports/${portId}`))
}

export async function fetchVulnDetail(vulnId: number) {
  return request<Vulnerability>(http.get(`/results/vulns/${vulnId}`))
}

// --- 仪表盘 API ---

export interface DashboardStats {
  kpi: {
    assets_total: number
    assets_domains: number
    tasks_running: number
    tasks_pending: number
    tasks_completed_today: number
    vulns_critical: number // [注] 对应后端返回的高危漏洞数
  }
  charts: {
    trend_dates: string[]
    trend_values: number[]
    vuln_distribution: Array<{ name: string; value: number }>
  }
  lists: {
    recent_assets: Array<{
      id: number
      name: string
      type: string
      created_at: string
    }>
  }
}

/**
 * [Dashboard] 获取仪表盘聚合数据
 */
export async function fetchDashboardStats() {
  return request<DashboardStats>(http.get('/stats/dashboard'))
}