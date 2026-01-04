import http, { request } from '@/api/http'

export interface ScanConfigSummary {
  name: string
  agent_type?: string | null
  description?: string | null
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
  created_at: string
  completed_at?: string | null
  log?: string | null
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
}

export async function fetchScanConfigs() {
  return request<ScanConfigSummary[]>(http.get('/scan-configs'))
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

export async function triggerScan(assetId: number, payload: { config_name: string }) {
  return request<ScanTask>(http.post(`/assets/${assetId}/scan`, payload))
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
  return request<PortSummary[]>(http.get(`/results/assets/${assetId}/ports`, { params }))
}

export async function fetchAssetWeb(
  assetId: number,
  params: { skip?: number; limit?: number } = {}
) {
  return request<HTTPServiceSummary[]>(http.get(`/results/assets/${assetId}/web`, { params }))
}

export async function fetchAssetVulns(
  assetId: number,
  params: { skip?: number; limit?: number } = {}
) {
  return request<VulnerabilitySummary[]>(http.get(`/results/assets/${assetId}/vulns`, { params }))
}

export async function listTasks(params: Record<string, unknown> = {}) {
  return request<ScanTask[]>(http.get('/tasks', { params }))
}
