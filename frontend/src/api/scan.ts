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

export interface ScanTask {
  id: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  config_name: string
  asset_id: number | null
  created_at: string
  completed_at?: string | null
  log?: string | null
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

export async function listTasks(params: Record<string, unknown> = {}) {
  return request<ScanTask[]>(http.get('/tasks', { params }))
}
