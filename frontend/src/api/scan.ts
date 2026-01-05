import http, { request } from '@/api/http'

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

export interface TaskListResponse {
  items: ScanTask[]
  total: number
}

export interface ScanSubmissionResponse {
  strategy_name: string
  task_ids: number[]
}

export interface TaskListResponse {
  items: ScanTask[]
  total: number
}

export interface ScanSubmissionResponse {
  strategy_name: string
  task_ids: number[]
}

export interface HostSummary {
  id: number
  hostname: string
  status: string
  created_at: string
  ips: string[]
  is_bookmarked: boolean
  project_id: number
  root_asset_id: number
}

export interface HostListResponse {
  items: HostSummary[]
  next_cursor: number | null
  has_more: boolean
  limit: number
}

export interface PortSummary {
  id: number
  ip: string
  port: number
  service?: string | null
  root_asset_id?: number | null
}

export interface HTTPServiceSummary {
  id: number
  url: string
  title?: string | null
  tech?: string | null
  status?: number | null
}

export interface VulnerabilitySummary {
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

export interface OffsetListResponse<T> {
  items: T[]
  next_offset: number | null
  has_more: boolean
  limit: number
}

export async function fetchScanStrategies() {
  return request<ScanStrategySummary[]>(http.get('/scan-strategies'))
}

export async function fetchProjects(params: { skip?: number; limit?: number; search?: string } = {}) {
  return request<Project[]>(http.get('/projects', { params }))
}

export async function createProject(payload: { name: string }) {
  return request<Project>(http.post('/projects', payload))
}

export async function createAsset(projectId: number, payload: { name: string; type: 'domain' | 'cidr' }) {
  return request<Asset>(http.post(`/projects/${projectId}/assets`, payload))
}

export async function triggerScan(assetId: number, payload: { strategy_name: string }) {
  return request<ScanSubmissionResponse>(http.post(`/assets/${assetId}/scan`, payload))
}


export async function fetchAssetsForProject(
  projectId: number,
  params: { skip?: number; limit?: number; search?: string } = {}
) {
  return request<Asset[]>(http.get(`/projects/${projectId}/assets`, { params }))
}

export async function fetchTask(taskId: number) {
  return request<ScanTask>(http.get(`/tasks/${taskId}`))
}

export async function retryTask(taskId: number, payload: { mode: 'strategy' | 'step' }) {
  return request<ScanSubmissionResponse>(http.post(`/tasks/${taskId}/retry`, payload))
}

export async function searchAssetsByName(name: string, limit = 10) {
  return request<AssetSearchResult[]>(http.get('/assets/search', { params: { name, limit } }))
}

export async function fetchAssetHosts(
  assetId: number,
  params: { limit?: number; cursor?: number | null } = {}
) {
  return request<HostListResponse>(http.get(`/results/assets/${assetId}/hosts`, { params }))
}

export async function fetchAssetPorts(
  assetId: number,
  params: { skip?: number; limit?: number } = {}
) {
  return request<OffsetListResponse<PortSummary>>(http.get(`/results/assets/${assetId}/ports`, { params }))
}

export async function fetchAssetWeb(
  assetId: number,
  params: { skip?: number; limit?: number } = {}
) {
  return request<OffsetListResponse<HTTPServiceSummary>>(http.get(`/results/assets/${assetId}/web`, { params }))
}

export async function fetchAssetVulns(
  assetId: number,
  params: { skip?: number; limit?: number } = {}
) {
  return request<OffsetListResponse<VulnerabilitySummary>>(http.get(`/results/assets/${assetId}/vulns`, { params }))
}

export async function fetchHostDetail(hostId: number) {
  return request<HostSummary>(http.get(`/results/hosts/${hostId}`))
}

export async function fetchPortDetail(portId: number) {
  return request<PortSummary>(http.get(`/results/ports/${portId}`))
}

export async function fetchVulnDetail(vulnId: number) {
  return request<VulnerabilitySummary>(http.get(`/results/vulns/${vulnId}`))
}

export async function listTasks(params: Record<string, unknown> = {}) {
  return request<ScanTask[]>(http.get('/tasks', { params }))
}

export async function fetchAssets(params: Record<string, unknown> = {}) {
  return request<Asset[]>(http.get('/assets', { params }))
}

export async function fetchAssetById(assetId: number) {
  return request<Asset>(http.get(`/assets/${assetId}`))
}
