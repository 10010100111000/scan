<template>
  <div class="scan-view">
    <header class="scan-view__header">
      <div>
        <p class="eyebrow">{{ copy.headerEyebrow }}</p>
        <h2>{{ copy.headerTitle }}</h2>
        <p class="subtitle">{{ copy.headerSubtitle }}</p>
      </div>
    </header>

    <section class="scan-view__body">
      <div class="scan-panel card-glass">
        <div class="form-grid">
          <div class="field">
            <label class="field-label">{{ copy.projectLabel }}</label>
            <el-select
              v-model="form.project_id"
              filterable
              remote
              clearable
              :placeholder="copy.projectPlaceholder"
              class="full-width"
              :remote-method="searchProjects"
              :loading="projectsLoading"
            >
              <el-option
                v-for="project in projects"
                :key="project.id"
                :label="projectOptionLabel(project)"
                :value="project.id"
              />
            </el-select>
            <div class="field-actions">
              <el-button text size="small" @click="loadProjects">{{ copy.refreshProjects }}</el-button>
            </div>
          </div>
          <div class="field">
            <label class="field-label">{{ copy.createProjectLabel }}</label>
            <div class="inline-row">
              <el-input v-model="newProjectName" clearable :placeholder="copy.projectNamePlaceholder" />
              <el-button
                type="primary"
                plain
                :disabled="!newProjectName"
                :loading="projectCreating"
                @click="handleCreateProject"
              >
                {{ copy.createButton }}
              </el-button>
            </div>
          </div>
        </div>

        <div class="search-box">
          <el-input v-model="form.target" size="large" clearable :placeholder="copy.targetPlaceholder">
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="form-grid">
          <div class="field">
            <label class="field-label">{{ copy.scanProfileLabel }}</label>
            <el-select
              v-model="form.config_name"
              filterable
              :placeholder="copy.scanProfilePlaceholder"
              class="full-width"
              :loading="scanConfigsLoading"
            >
              <el-option v-for="cfg in scanConfigs" :key="cfg.name" :label="cfg.name" :value="cfg.name">
                <div class="option-row">
                  <strong>{{ cfg.name }}</strong>
                  <span class="text-faint">{{ cfg.description || copy.noDescription }}</span>
                </div>
              </el-option>
            </el-select>
          </div>
        </div>

        <div class="actions">
          <el-button
            type="primary"
            size="large"
            :loading="scanSubmitting"
            :disabled="!form.target || !form.config_name || scanSubmitting"
            @click="handleStartScan"
          >
            {{ copy.startScan }}
          </el-button>
          <el-button text @click="resetForm">{{ copy.reset }}</el-button>
        </div>

        <div class="scan-meta">
          <div>
            <p class="text-faint">{{ copy.currentProject }}</p>
            <strong>{{ projectLabel }}</strong>
          </div>
          <div>
            <p class="text-faint">{{ copy.targetLabel }}</p>
            <strong>{{ currentTargetLabel }}</strong>
          </div>
          <div v-if="lastTask">
            <p class="text-faint">{{ copy.latestTask }}</p>
            <strong>#{{ lastTask.id }} ? {{ lastTask.status }}</strong>
          </div>
        </div>

        <div v-if="scanRunning" class="scan-progress">
          <div class="scan-progress__ring">
            <el-icon class="is-loading"><Loading /></el-icon>
          </div>
          <h3>{{ copy.scanRunningTitle }}</h3>
          <p class="text-faint">{{ copy.scanRunningDesc.replace('{id}', String(lastTask?.id ?? '')) }}</p>
          <div class="progress-steps">
            <div
              v-for="(step, index) in progressSteps"
              :key="step"
              :class="['progress-step', { active: index <= progressStepIndex }]"
            >
              <span class="progress-dot"></span>
              <span>{{ step }}</span>
            </div>
          </div>
          <el-button text :loading="scanStatusLoading" @click="refreshTaskStatus">{{ copy.refreshStatus }}</el-button>
        </div>

        <div class="divider"></div>

        <div class="results-header">
          <div>
            <p class="eyebrow">{{ copy.resultsEyebrow }}</p>
            <h3>{{ copy.resultsTitle }}</h3>
            <p class="text-faint">{{ copy.resultsHint }}</p>
          </div>
          <div class="results-actions">
            <el-button size="small" :loading="resultsLoading" @click="refreshResults">{{ copy.refreshResults }}</el-button>
            <el-button size="small" text @click="clearResults">{{ copy.clearResults }}</el-button>
          </div>
        </div>

        <div class="results-summary">
          <div class="summary-card">
            <p class="text-faint">{{ copy.summarySubdomains }}</p>
            <strong>{{ hosts.length }}</strong>
          </div>
          <div class="summary-card">
            <p class="text-faint">{{ copy.summaryPorts }}</p>
            <strong>{{ ports.length }}</strong>
          </div>
          <div class="summary-card">
            <p class="text-faint">{{ copy.summaryWeb }}</p>
            <strong>{{ webServices.length }}</strong>
          </div>
          <div class="summary-card">
            <p class="text-faint">{{ copy.summaryVulns }}</p>
            <strong>{{ vulnerabilities.length }}</strong>
          </div>
        </div>

        <el-tabs v-model="resultsTab" class="results-tabs" @tab-change="handleTabChange">
          <el-tab-pane :label="copy.tabSubdomains" name="hosts">
            <div v-if="hosts.length === 0" class="empty-wrap">
              <el-empty :description="copy.emptySubdomains" />
            </div>
            <div v-else class="result-list">
              <div v-for="host in hosts" :key="host.id" class="result-row">
                <div>
                  <strong>{{ host.hostname }}</strong>
                  <p class="text-faint">{{ host.ips.join(', ') || copy.noIpMapped }}</p>
                </div>
                <div class="result-meta">
                  <el-tag size="small" effect="plain">{{ host.status }}</el-tag>
                  <span class="text-faint">{{ formatTime(host.created_at) }}</span>
                </div>
              </div>
              <div v-if="hostsHasMore" class="load-more">
                <el-button text :loading="hostsLoading" @click="loadMoreHosts">{{ copy.loadMore }}</el-button>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane :label="copy.tabPorts" name="ports">
            <div v-if="ports.length === 0" class="empty-wrap">
              <el-empty :description="copy.emptyPorts" />
            </div>
            <div v-else class="result-list">
              <div v-for="port in ports" :key="port.id" class="result-row">
                <div>
                  <strong>{{ port.ip }}:{{ port.port }}</strong>
                  <p class="text-faint">{{ port.service || 'unknown' }}</p>
                </div>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane :label="copy.tabWeb" name="web">
            <div v-if="webServices.length === 0" class="empty-wrap">
              <el-empty :description="copy.emptyWeb" />
            </div>
            <div v-else class="result-list">
              <div v-for="service in webServices" :key="service.id" class="result-row">
                <div>
                  <strong>{{ service.url }}</strong>
                  <p class="text-faint">{{ service.title || copy.untitled }}</p>
                  <p class="text-faint">{{ service.tech || copy.noTech }}</p>
                </div>
                <div class="result-meta">
                  <el-tag size="small" effect="plain">{{ service.status || 'n/a' }}</el-tag>
                </div>
              </div>
            </div>
          </el-tab-pane>
          <el-tab-pane :label="copy.tabVulns" name="vulns">
            <div v-if="vulnerabilities.length === 0" class="empty-wrap">
              <el-empty :description="copy.emptyVulns" />
            </div>
            <div v-else class="result-list">
              <div v-for="vuln in vulnerabilities" :key="vuln.id" class="result-row">
                <div>
                  <strong>{{ vuln.name }}</strong>
                  <p class="text-faint">{{ vuln.url || copy.noTarget }}</p>
                </div>
                <div class="result-meta">
                  <el-tag :type="severityType(vuln.severity)" size="small" effect="dark">{{ vuln.severity }}</el-tag>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <aside class="scan-aside card-glass">
        <h3>{{ copy.tipsTitle }}</h3>
        <ul>
          <li>{{ copy.tipProfiles }} <code>scanners.yaml</code>?</li>
          <li>{{ copy.tipSubfinder }}</li>
          <li>{{ copy.tipProject }}</li>
        </ul>
        <div class="aside-meta">
          <div>
            <p class="text-faint">{{ copy.summaryProfiles }}</p>
            <strong>{{ scanConfigs.length }}</strong>
          </div>
          <div>
            <p class="text-faint">{{ copy.summaryProjects }}</p>
            <strong>{{ projects.length }}</strong>
          </div>
        </div>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Search } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import {
  createAsset,
  createProject,
  fetchAssetHosts,
  fetchAssetPorts,
  fetchAssetVulns,
  fetchAssetWeb,
  fetchAssetsForProject,
  fetchProjects,
  fetchScanConfigs,
  fetchTask,
  searchAssetsByName,
  triggerScan,
  type HostSummary,
  type HTTPServiceSummary,
  type PortSummary,
  type Project,
  type ScanConfigSummary,
  type ScanTask,
  type VulnerabilitySummary,
} from '@/api/scan'

const copy = {
  headerEyebrow: '新建扫描',
  headerTitle: '发起扫描',
  headerSubtitle: '选择项目、目标与 Scan profile，任务在后台执行。',
  projectLabel: '项目',
  projectPlaceholder: '选择或搜索项目',
  refreshProjects: '刷新项目',
  createProjectLabel: '新建项目（可选）',
  projectNamePlaceholder: '项目名称',
  createButton: '创建',
  targetPlaceholder: '域名 / IP / CIDR',
  scanProfileLabel: 'Scan profile',
  scanProfilePlaceholder: '选择 Scan profile',
  noDescription: '暂无描述',
  startScan: '开始扫描',
  reset: '重置',
  currentProject: '当前项目',
  targetLabel: '目标',
  latestTask: '最近任务',
  scanRunningTitle: '扫描任务正在后台执行',
  scanRunningDesc: '任务 {id} 已排队，系统将自动刷新状态。',
  refreshStatus: '刷新状态',
  resultsEyebrow: '结果',
  resultsTitle: '扫描结果',
  resultsHint: '扫描完成后刷新以获取最新数据。',
  refreshResults: '刷新结果',
  clearResults: '清空',
  summarySubdomains: '子域名',
  summaryPorts: '开放端口',
  summaryWeb: 'Web 服务',
  summaryVulns: '漏洞',
  tabSubdomains: '子域名',
  tabPorts: '端口',
  tabWeb: 'Web',
  tabVulns: '漏洞',
  emptySubdomains: '暂无子域名',
  emptyPorts: '暂无端口',
  emptyWeb: '暂无 Web 服务',
  emptyVulns: '暂无漏洞',
  noIpMapped: '未解析到 IP',
  loadMore: '加载更多',
  untitled: '无标题',
  noTech: '无技术指纹',
  noTarget: '无目标',
  tipsTitle: '提示',
  tipProfiles: 'Scan profile 来自后端',
  tipSubfinder: 'Subfinder 结果展示在「子域名」标签。',
  tipProject: '建议选择项目以归类结果。',
  summaryProfiles: '配置数',
  summaryProjects: '项目数',
  msgProjectCreated: '项目已创建：',
  msgSelectProject: '请选择或创建项目',
  msgEnterTarget: '请输入目标',
  msgSelectProfile: '请选择 Scan profile',
  msgTaskCreated: '任务 #',
  msgTaskCreatedSuffix: ' 已创建',
  msgNoAsset: '尚未选择资产',
  msgFoundExisting: '已在项目 #',
  msgFoundExistingSuffix: ' 找到资产，直接加载结果。',
  progressSteps: ['排队中', '扫描中', '解析入库', '完成'],
  notSelected: '未选择',
  notSet: '未设置',
}

const scanConfigs = ref<ScanConfigSummary[]>([])
const scanConfigsLoading = ref(false)
const scanSubmitting = ref(false)
const scanStatusLoading = ref(false)
const scanRunning = ref(false)

const projects = ref<Project[]>([])
const projectsLoading = ref(false)
const projectCreating = ref(false)
const newProjectName = ref('')

const lastTask = ref<ScanTask | null>(null)
const lastTaskStatus = ref<ScanTask['status'] | null>(null)
const currentAssetId = ref<number | null>(null)
const currentTarget = ref('')
let pollTimer: number | null = null

const form = reactive<{
  target: string
  config_name: string
  project_id: number | null
}>({
  target: '',
  config_name: '',
  project_id: null,
})

const progressSteps = copy.progressSteps

const resultsTab = ref<'hosts' | 'ports' | 'web' | 'vulns'>('hosts')
const resultsLoading = ref(false)
const hostsLoading = ref(false)
const hosts = ref<HostSummary[]>([])
const hostsCursor = ref<number | null>(null)
const hostsHasMore = ref(false)
const ports = ref<PortSummary[]>([])
const webServices = ref<HTTPServiceSummary[]>([])
const vulnerabilities = ref<VulnerabilitySummary[]>([])

const projectLabel = computed(() => {
  const project = projects.value.find((item) => item.id === form.project_id)
  if (project) {
    return `${project.name} (#${project.id})`
  }
  return copy.notSelected
})

const currentTargetLabel = computed(() => currentTarget.value || copy.notSet)

const progressStepIndex = computed(() => {
  if (!lastTask.value) {
    return 0
  }
  switch (lastTask.value.status) {
    case 'pending':
      return 0
    case 'running':
      return 1
    case 'completed':
      return 3
    case 'failed':
      return 3
    default:
      return 0
  }
})

const projectOptionLabel = (project: Project) => `${project.name} (#${project.id})`

const formatTime = (value?: string | null) => (value ? dayjs(value).format('YYYY-MM-DD HH:mm') : 'n/a')

const detectAssetType = (target: string) => {
  const value = target.trim()
  if (!value) {
    return 'domain'
  }
  if (value.includes('/')) {
    return 'cidr'
  }
  const ipv4Regex = /^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$/
  if (ipv4Regex.test(value)) {
    return 'cidr'
  }
  if (value.includes(':')) {
    return 'cidr'
  }
  return 'domain'
}

const severityType = (severity: string) => {
  switch (severity) {
    case 'critical':
    case 'high':
      return 'danger'
    case 'medium':
      return 'warning'
    case 'low':
      return 'info'
    default:
      return 'info'
  }
}

const loadProjects = async (search = '') => {
  projectsLoading.value = true
  try {
    projects.value = await fetchProjects({ search, limit: 20 })
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    projectsLoading.value = false
  }
}

const searchProjects = async (query: string) => {
  await loadProjects(query)
}

const handleCreateProject = async () => {
  const name = newProjectName.value.trim()
  if (!name) {
    return
  }
  projectCreating.value = true
  try {
    const project = await createProject({ name })
    projects.value = [project, ...projects.value]
    form.project_id = project.id
    newProjectName.value = ''
    ElMessage.success(`${copy.msgProjectCreated}${project.name}`)
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    projectCreating.value = false
  }
}

const loadConfigs = async () => {
  scanConfigsLoading.value = true
  try {
    scanConfigs.value = await fetchScanConfigs()
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    scanConfigsLoading.value = false
  }
}

const ensureProjectId = async () => {
  if (form.project_id) {
    return form.project_id
  }
  const name = newProjectName.value.trim()
  if (!name) {
    ElMessage.warning(copy.msgSelectProject)
    return null
  }
  const project = await createProject({ name })
  projects.value = [project, ...projects.value]
  form.project_id = project.id
  newProjectName.value = ''
  return project.id
}

const resolveAssetId = async (projectId: number, target: string) => {
  const assets = await fetchAssetsForProject(projectId, { search: target, limit: 5 })
  const targetKey = target.toLowerCase()
  const existing = assets.find((asset) => asset.name.toLowerCase() === targetKey)
  if (existing) {
    return existing.id
  }
  const asset = await createAsset(projectId, { name: target, type: detectAssetType(target) })
  return asset.id
}

const startPolling = () => {
  if (!lastTask.value) {
    return
  }
  stopPolling()
  pollTimer = window.setInterval(async () => {
    await refreshTaskStatus(true)
  }, 5000)
}

const stopPolling = () => {
  if (pollTimer) {
    window.clearInterval(pollTimer)
    pollTimer = null
  }
}

const refreshTaskStatus = async (silent = false) => {
  if (!lastTask.value) {
    return
  }
  if (!silent) {
    scanStatusLoading.value = true
  }
  try {
    const task = await fetchTask(lastTask.value.id)
    lastTask.value = task
    scanRunning.value = task.status === 'pending' || task.status === 'running'
    if (lastTaskStatus.value !== task.status && task.status === 'completed') {
      await refreshResults()
    }
    lastTaskStatus.value = task.status
    if (!scanRunning.value) {
      stopPolling()
    }
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    if (!silent) {
      scanStatusLoading.value = false
    }
  }
}

const loadHosts = async (reset = true) => {
  if (!currentAssetId.value) {
    return
  }
  hostsLoading.value = true
  try {
    const response = await fetchAssetHosts(currentAssetId.value, {
      limit: 80,
      cursor: reset ? undefined : hostsCursor.value ?? undefined,
    })
    if (reset) {
      hosts.value = response.items
    } else {
      hosts.value = [...hosts.value, ...response.items]
    }
    hostsCursor.value = response.next_cursor
    hostsHasMore.value = response.has_more
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    hostsLoading.value = false
  }
}

const loadMoreHosts = async () => {
  if (!hostsHasMore.value) {
    return
  }
  await loadHosts(false)
}

const loadPorts = async () => {
  if (!currentAssetId.value) {
    return
  }
  ports.value = await fetchAssetPorts(currentAssetId.value, { limit: 200 })
}

const loadWeb = async () => {
  if (!currentAssetId.value) {
    return
  }
  webServices.value = await fetchAssetWeb(currentAssetId.value, { limit: 200 })
}

const loadVulns = async () => {
  if (!currentAssetId.value) {
    return
  }
  vulnerabilities.value = await fetchAssetVulns(currentAssetId.value, { limit: 200 })
}

const refreshResults = async () => {
  if (!currentAssetId.value) {
    ElMessage.warning(copy.msgNoAsset)
    return
  }
  resultsLoading.value = true
  try {
    await loadHosts(true)
    await Promise.all([loadPorts(), loadWeb(), loadVulns()])
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    resultsLoading.value = false
  }
}

const clearResults = () => {
  hosts.value = []
  hostsCursor.value = null
  hostsHasMore.value = false
  ports.value = []
  webServices.value = []
  vulnerabilities.value = []
}

const handleTabChange = async (name: string | number) => {
  const tab = name as 'hosts' | 'ports' | 'web' | 'vulns'
  if (!currentAssetId.value) {
    return
  }
  if (tab === 'hosts' && hosts.value.length === 0) {
    await loadHosts(true)
  }
  if (tab === 'ports' && ports.value.length === 0) {
    await loadPorts()
  }
  if (tab === 'web' && webServices.value.length === 0) {
    await loadWeb()
  }
  if (tab === 'vulns' && vulnerabilities.value.length === 0) {
    await loadVulns()
  }
}

const handleStartScan = async () => {
  const rawTarget = form.target.trim()
  const normalizedTarget = rawTarget.replace(/\.+$/, '').toLowerCase()
  if (!normalizedTarget) {
    ElMessage.warning(copy.msgEnterTarget)
    return
  }
  if (!form.config_name) {
    ElMessage.warning(copy.msgSelectProfile)
    return
  }
  scanSubmitting.value = true
  try {
    const existingAssets = await searchAssetsByName(normalizedTarget, 1)
    if (existingAssets.length > 0) {
      const asset = existingAssets[0]
      currentAssetId.value = asset.id
      currentTarget.value = asset.name
      form.project_id = asset.project_id
      scanRunning.value = false
      lastTask.value = null
      lastTaskStatus.value = null
      await refreshResults()
      ElMessage.success(`${copy.msgFoundExisting}${asset.project_id}${copy.msgFoundExistingSuffix}`)
      return
    }
    const projectId = await ensureProjectId()
    if (!projectId) {
      return
    }
    const assetId = await resolveAssetId(projectId, normalizedTarget)
    currentAssetId.value = assetId
    currentTarget.value = normalizedTarget
    const task = await triggerScan(assetId, { config_name: form.config_name })
    lastTask.value = task
    lastTaskStatus.value = task.status
    scanRunning.value = task.status === 'pending' || task.status === 'running'
    ElMessage.success(`${copy.msgTaskCreated}${task.id}${copy.msgTaskCreatedSuffix}`)
    startPolling()
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    scanSubmitting.value = false
  }
}

const resetForm = () => {
  form.target = ''
  form.config_name = ''
}

onMounted(async () => {
  await Promise.all([loadProjects(), loadConfigs()])
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.scan-view {
  min-height: 100%;
  padding: 32px 48px;
  color: #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: radial-gradient(circle at 15% 15%, rgba(56, 189, 248, 0.08), transparent 35%),
    radial-gradient(circle at 75% 10%, rgba(34, 197, 94, 0.08), transparent 40%),
    #0b1020;
}

.scan-view__header h2 {
  margin: 6px 0 8px;
  font-size: 28px;
}

.eyebrow {
  margin: 0;
  font-size: 12px;
  letter-spacing: 0.18em;
  color: #94a3b8;
}

.subtitle {
  margin: 0;
  color: #9ca3af;
}

.scan-view__body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 20px;
  align-items: start;
}

.card-glass {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 18px;
  box-shadow: 0 28px 80px rgba(2, 6, 23, 0.45);
}

.scan-panel {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.search-box :deep(.el-input__wrapper) {
  background: rgba(2, 6, 23, 0.4);
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: none;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-label {
  font-size: 13px;
  color: #cbd5f5;
}

.field-actions {
  margin-top: 4px;
}

.inline-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
}

.full-width {
  width: 100%;
}

.option-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.scan-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  padding-top: 8px;
  border-top: 1px solid rgba(148, 163, 184, 0.12);
}

.scan-progress {
  margin-top: 4px;
  padding: 18px 16px;
  border-radius: 16px;
  background: rgba(2, 6, 23, 0.5);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 12px;
  min-height: 220px;
}

.scan-progress__ring {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: 1px solid rgba(148, 163, 184, 0.3);
  display: grid;
  place-items: center;
  color: #67e8f9;
}

.progress-steps {
  width: 100%;
  display: grid;
  gap: 8px;
}

.progress-step {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #64748b;
}

.progress-step.active {
  color: #e2e8f0;
}

.progress-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(148, 163, 184, 0.4);
}

.progress-step.active .progress-dot {
  background: #38bdf8;
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.6);
}

.divider {
  height: 1px;
  background: rgba(148, 163, 184, 0.14);
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.results-actions {
  display: flex;
  gap: 8px;
}

.results-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.summary-card {
  background: rgba(2, 6, 23, 0.45);
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 14px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.results-tabs :deep(.el-tabs__item) {
  color: #94a3b8;
}

.results-tabs :deep(.el-tabs__item.is-active) {
  color: #e2e8f0;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(2, 6, 23, 0.4);
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.result-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-end;
}

.load-more {
  display: flex;
  justify-content: center;
}

.empty-wrap {
  padding: 16px 0 4px;
}

.scan-aside {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.scan-aside h3 {
  margin: 0;
}

.scan-aside ul {
  margin: 0;
  padding-left: 18px;
  color: #cbd5e1;
  line-height: 1.6;
}

.aside-meta {
  display: flex;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid rgba(148, 163, 184, 0.12);
}

.text-faint {
  color: #94a3b8;
}

@media (max-width: 1100px) {
  .scan-view {
    padding: 24px;
  }

  .scan-view__body {
    grid-template-columns: 1fr;
  }

  .results-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 640px) {
  .scan-view__header h2 {
    font-size: 22px;
  }

  .scan-meta {
    grid-template-columns: 1fr;
  }

  .result-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .result-meta {
    align-items: flex-start;
  }
}
</style>
