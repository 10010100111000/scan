<template>
  <div class="scan-view">
    <header class="scan-view__header">
      <div>
        <p class="eyebrow">新建扫描</p>
        <h2>发起扫描任务</h2>
        <p class="subtitle">选择目标与扫描策略即可开始，项目用于结果归档（可选）。</p>
      </div>
    </header>

    <section class="scan-view__body">
      <div class="scan-panel card-glass">
        <div class="form-grid">
          <div class="field">
            <label class="field-label">项目（可选）</label>
            <el-select
              v-model="form.project_id"
              filterable
              remote
              clearable
              :disabled="useGlobalProject"
              placeholder="选择或搜索项目"
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
              <el-button text size="small" @click="loadProjects">刷新项目</el-button>
            </div>
            <p class="field-hint">项目用于归档，不选择则自动归档到默认项目。</p>
          </div>
          <div class="field">
            <label class="field-label">新建项目（可选）</label>
            <div class="inline-row">
              <el-input v-model="newProjectName" clearable placeholder="项目名称" />
              <el-button
                type="primary"
                plain
                :disabled="!newProjectName"
                :loading="projectCreating"
                @click="handleCreateProject"
              >
                创建
              </el-button>
            </div>
            <div class="field-actions">
              <el-switch v-model="useGlobalProject" active-text="全局扫描（默认项目）" />
            </div>
          </div>
        </div>

        <div class="search-box">
          <el-input v-model="form.target" size="large" clearable placeholder="域名 / IP / CIDR">
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="form-grid">
          <div class="field">
            <label class="field-label">扫描策略</label>
            <el-select
              v-model="form.strategy_name"
              filterable
              placeholder="选择扫描策略"
              class="full-width"
              :loading="scanStrategiesLoading"
            >
              <el-option
                v-for="strategy in scanStrategies"
                :key="strategy.strategy_name"
                :label="strategy.strategy_name"
                :value="strategy.strategy_name"
              >
                <div class="option-row">
                  <strong>{{ strategy.strategy_name }}</strong>
                  <span class="text-faint">{{ strategy.description || '暂无描述' }}</span>
                  <span class="text-faint">步骤：{{ strategy.steps.join(' → ') }}</span>
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
            :disabled="!form.target || !form.strategy_name || scanSubmitting"
            @click="handleStartScan"
          >
            开始扫描
          </el-button>
          <el-button text @click="resetForm">重置</el-button>
        </div>

        <div v-if="lastSubmission.status !== 'idle'" :class="['status-banner', lastSubmission.status]">
          <div class="status-title">
            <strong>{{ lastSubmission.title }}</strong>
            <span class="text-faint">{{ lastSubmission.timestamp }}</span>
          </div>
          <p>{{ lastSubmission.message }}</p>
          <div v-if="lastSubmission.taskId" class="status-meta">
            <span class="text-faint">任务 ID</span>
            <strong>#{{ lastSubmission.taskId }}</strong>
          </div>
          <div v-if="lastAssetId && lastSubmission.status === 'success'" class="status-actions">
            <el-button size="small" type="primary" plain @click="goToResultDetail">查看结果详情</el-button>
          </div>
        </div>

        <div class="scan-meta">
          <div>
            <p class="text-faint">当前项目</p>
            <strong>{{ projectLabel }}</strong>
          </div>
          <div>
            <p class="text-faint">目标</p>
            <strong>{{ currentTargetLabel }}</strong>
          </div>
        </div>

        <div class="terminal">
          <div class="terminal-header">
            <span class="terminal-dot red"></span>
            <span class="terminal-dot yellow"></span>
            <span class="terminal-dot green"></span>
            <span class="terminal-title">任务终端</span>
            <span class="terminal-subtitle text-faint">显示最新提交日志</span>
          </div>
          <div class="terminal-body">
            <div v-if="terminalLines.length === 0" class="terminal-line text-faint">
              等待任务提交...
            </div>
            <div v-for="(line, index) in terminalLines" :key="index" class="terminal-line">
              {{ line }}
            </div>
          </div>
          <div class="terminal-footer">
            <span class="text-faint">状态：</span>
            <span :class="['terminal-status', terminalStatus]">{{ terminalStatusLabel }}</span>
          </div>
        </div>
      </div>

      <aside class="scan-aside card-glass">
        <h3>提示</h3>
        <ul>
          <li>扫描策略来自 <code>scan_strategies.yaml</code>，会编排多个扫描步骤。</li>
          <li>策略步骤会引用 <code>scanners.yaml</code> 中的扫描配置。</li>
          <li>项目是归档维度，不选择时系统会使用默认项目。</li>
          <li>域名类目标更关注子域名与 Web，IP/CIDR 更关注端口与服务。</li>
          <li>同名资产会直接复用，不重复发起任务。</li>
        </ul>
        <div class="aside-meta">
          <div>
            <p class="text-faint">可用策略</p>
            <strong>{{ scanStrategies.length }}</strong>
          </div>
          <div>
            <p class="text-faint">项目数量</p>
            <strong>{{ projects.length }}</strong>
          </div>
        </div>

        <div class="aside-section">
          <div class="task-header">
            <h3>任务状态</h3>
            <el-button text size="small" :loading="taskLoading" @click="refreshTaskStatus">
              刷新状态
            </el-button>
          </div>
          <div v-if="lastAssetId === null" class="text-faint">提交任务后显示最新状态。</div>
          <div v-else-if="taskList.length === 0" class="text-faint">暂无任务状态。</div>
          <ul v-else class="task-list">
            <li v-for="task in taskList" :key="task.id" class="task-item">
              <div>
                <strong>#{{ task.id }}</strong>
                <span class="text-faint"> · {{ task.config_name }}</span>
              </div>
              <span :class="['task-status-pill', task.status]">{{ task.status }}</span>
            </li>
          </ul>
        </div>

        <div class="aside-section">
          <div class="task-header">
            <h3>结果入口</h3>
          </div>
          <div v-if="lastAssetId === null" class="text-faint">提交任务后可查看结果详情。</div>
          <div v-else class="result-entry">
            <el-button type="primary" plain size="small" @click="goToResultDetail">
              查看结果详情
            </el-button>
            <p class="text-faint">根据目标类型展示子域名、端口、Web 与漏洞。</p>
          </div>
        </div>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import {
  createAsset,
  createProject,
  fetchAssetsForProject,
  fetchProjects,
  fetchScanStrategies,
  listTasks,
  searchAssetsByName,
  triggerScan,
  type Project,
  type ScanTask,
  type ScanStrategySummary,
} from '@/api/scan'
import { useScanOverlay } from '@/composables/useScanOverlay'
const { close: closeScan } = useScanOverlay()
const router = useRouter()

const scanStrategies = ref<ScanStrategySummary[]>([])
const scanStrategiesLoading = ref(false)
const scanSubmitting = ref(false)
const useGlobalProject = ref(true)
const DEFAULT_PROJECT_NAME = '默认项目'

const projects = ref<Project[]>([])
const projectsLoading = ref(false)
const projectCreating = ref(false)
const newProjectName = ref('')
const currentTarget = ref('')
const terminalLines = ref<string[]>([])
const terminalStatus = ref<'idle' | 'pending' | 'success' | 'failed'>('idle')
let autoCloseTimer: number | null = null
let taskPollTimer: number | null = null
const lastSubmission = reactive<{
  status: 'idle' | 'pending' | 'success' | 'failed'
  title: string
  message: string
  taskId: number | null
  timestamp: string
}>({
  status: 'idle',
  title: '',
  message: '',
  taskId: null,
  timestamp: '',
})
const lastAssetId = ref<number | null>(null)
const taskList = ref<ScanTask[]>([])
const taskLoading = ref(false)

const form = reactive<{
  target: string
  strategy_name: string
  project_id: number | null
}>({
  target: '',
  strategy_name: '',
  project_id: null,
})

const projectLabel = computed(() => {
  const project = projects.value.find((item) => item.id === form.project_id)
  if (project) {
    return `${project.name} (#${project.id})`
  }
  return '未选择'
})

const currentTargetLabel = computed(() => currentTarget.value || '未设置')

const terminalStatusLabel = computed(() => {
  switch (terminalStatus.value) {
    case 'pending':
      return '提交中'
    case 'success':
      return '已提交'
    case 'failed':
      return '失败'
    default:
      return '空闲'
  }
})

const projectOptionLabel = (project: Project) => `${project.name} (#${project.id})`

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
  if (useGlobalProject.value) {
    ElMessage.warning('全局扫描模式下将使用默认项目，无需创建新项目')
    return
  }
  projectCreating.value = true
  try {
    const project = await createProject({ name })
    projects.value = [project, ...projects.value]
    form.project_id = project.id
    newProjectName.value = ''
    ElMessage.success(`项目已创建：${project.name}`)
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    projectCreating.value = false
  }
}

const loadStrategies = async () => {
  scanStrategiesLoading.value = true
  try {
    scanStrategies.value = await fetchScanStrategies()
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    scanStrategiesLoading.value = false
  }
}

const refreshTaskStatus = async () => {
  if (lastAssetId.value === null) {
    return
  }
  taskLoading.value = true
  try {
    taskList.value = await listTasks({ asset_id: lastAssetId.value, limit: 20 })
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    taskLoading.value = false
  }
}

const goToResultDetail = () => {
  if (!lastAssetId.value) {
    ElMessage.warning('暂无可查看的结果')
    return
  }
  router.push({ name: 'Results', params: { assetId: lastAssetId.value } })
}

const ensureProjectId = async () => {
  // 全局扫描模式：自动使用默认项目
  if (useGlobalProject.value) {
    const cached = projects.value.find((item) => item.name === DEFAULT_PROJECT_NAME)
    if (cached) {
      return cached.id
    }
    const existing = await fetchProjects({ search: DEFAULT_PROJECT_NAME, limit: 1 })
    if (existing.length > 0 && existing[0].name === DEFAULT_PROJECT_NAME) {
      projects.value = [existing[0], ...projects.value]
      return existing[0].id
    }
    const created = await createProject({ name: DEFAULT_PROJECT_NAME })
    projects.value = [created, ...projects.value]
    return created.id
  }
  if (form.project_id) {
    return form.project_id
  }
  const name = newProjectName.value.trim()
  if (!name) {
    ElMessage.warning('请选择或创建项目')
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

const handleStartScan = async () => {
  const rawTarget = form.target.trim()
  const normalizedTarget = rawTarget.replace(/\.+$/, '').toLowerCase()
  if (!normalizedTarget) {
    ElMessage.warning('请输入目标')
    return
  }
  if (!form.strategy_name) {
    ElMessage.warning('请选择扫描策略')
    return
  }
  scanSubmitting.value = true
  try {
    terminalLines.value = []
    terminalStatus.value = 'pending'
    lastSubmission.status = 'pending'
    lastSubmission.title = '提交中'
    lastSubmission.message = '正在创建资产并提交扫描任务...'
    lastSubmission.taskId = null
    lastSubmission.timestamp = new Date().toLocaleTimeString()
    if (autoCloseTimer) {
      window.clearTimeout(autoCloseTimer)
      autoCloseTimer = null
    }

    const existingAssets = await searchAssetsByName(normalizedTarget, 1)
    if (existingAssets.length > 0) {
      currentTarget.value = existingAssets[0].name
      form.project_id = existingAssets[0].project_id
      lastAssetId.value = existingAssets[0].id
      terminalLines.value.push('目标已存在，直接复用历史结果。')
      terminalStatus.value = 'success'
      lastSubmission.status = 'success'
      lastSubmission.title = '复用历史结果'
      lastSubmission.message = '目标已存在，未重复提交新的扫描任务。'
      lastSubmission.taskId = null
      lastSubmission.timestamp = new Date().toLocaleTimeString()
      ElMessage.success('已存在资产，结果将直接复用')
      autoCloseTimer = window.setTimeout(() => {
        closeScan()
      }, 1800)
      return
    }

    const projectId = await ensureProjectId()
    if (!projectId) {
      return
    }
    const assetId = await resolveAssetId(projectId, normalizedTarget)
    currentTarget.value = normalizedTarget
    lastAssetId.value = assetId
    const submission = await triggerScan(assetId, { strategy_name: form.strategy_name })
    if (submission.task_ids.length === 0) {
      terminalLines.value.push('已存在相关结果，未重复触发扫描。')
      terminalStatus.value = 'success'
      lastSubmission.status = 'success'
      lastSubmission.title = '复用历史结果'
      lastSubmission.message = '数据库已存在相关扫描结果，本次未重复提交任务。'
      lastSubmission.taskId = null
      lastSubmission.timestamp = new Date().toLocaleTimeString()
      ElMessage.success('已存在结果，未重复提交')
    } else {
      terminalLines.value.push(`任务已提交：${submission.task_ids.join(', ')}。`)
      terminalStatus.value = 'success'
      lastSubmission.status = 'success'
      lastSubmission.title = '提交成功'
      lastSubmission.message = '扫描任务已进入队列，稍后可在任务列表查看进度。'
      lastSubmission.taskId = submission.task_ids[0] ?? null
      lastSubmission.timestamp = new Date().toLocaleTimeString()
      ElMessage.success('扫描任务已提交')
    }
    autoCloseTimer = window.setTimeout(() => {
      closeScan()
    }, 1800)
    await refreshTaskStatus()
  } catch (error) {
    terminalLines.value.push(`推送失败：${(error as Error).message}`)
    terminalStatus.value = 'failed'
    lastSubmission.status = 'failed'
    lastSubmission.title = '提交失败'
    lastSubmission.message = (error as Error).message || '请稍后重试'
    lastSubmission.taskId = null
    lastSubmission.timestamp = new Date().toLocaleTimeString()
    ElMessage.error((error as Error).message)
  } finally {
    scanSubmitting.value = false
  }
}

const resetForm = () => {
  form.target = ''
  form.strategy_name = ''
}

onMounted(async () => {
  await Promise.all([loadProjects(), loadStrategies()])
  taskPollTimer = window.setInterval(() => {
    refreshTaskStatus()
  }, 5000)
})

onUnmounted(() => {
  if (autoCloseTimer) {
    window.clearTimeout(autoCloseTimer)
  }
  if (taskPollTimer) {
    window.clearInterval(taskPollTimer)
  }
})

watch(
  () => form.project_id,
  (value) => {
    if (value) {
      useGlobalProject.value = false
    }
  }
)

watch(useGlobalProject, (enabled) => {
  if (enabled) {
    form.project_id = null
  }
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

.field-hint {
  margin: 4px 0 0;
  font-size: 12px;
  color: #94a3b8;
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

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 8px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
}

.task-status-pill {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  text-transform: capitalize;
  border: 1px solid transparent;
}

.task-status-pill.pending {
  color: #fbbf24;
  border-color: rgba(251, 191, 36, 0.35);
}

.task-status-pill.running {
  color: #38bdf8;
  border-color: rgba(56, 189, 248, 0.35);
}

.task-status-pill.completed {
  color: #22c55e;
  border-color: rgba(34, 197, 94, 0.35);
}

.task-status-pill.failed {
  color: #f87171;
  border-color: rgba(248, 113, 113, 0.35);
}

.result-entry {
  display: grid;
  gap: 8px;
}

.terminal {
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(2, 6, 23, 0.55);
  overflow: hidden;
}

.terminal-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(15, 23, 42, 0.7);
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.terminal-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.terminal-dot.red {
  background: #ef4444;
}

.terminal-dot.yellow {
  background: #fbbf24;
}

.terminal-dot.green {
  background: #22c55e;
}

.terminal-title {
  font-size: 12px;
  color: #94a3b8;
  margin-left: 6px;
}

.terminal-subtitle {
  margin-left: auto;
  font-size: 12px;
}

.terminal-body {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-family: 'JetBrains Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', monospace;
  font-size: 12px;
  color: #e2e8f0;
  min-height: 140px;
  max-height: 220px;
  overflow: auto;
  white-space: pre-wrap;
}

.terminal-line {
  line-height: 1.5;
}

.terminal-footer {
  padding: 8px 12px;
  border-top: 1px solid rgba(148, 163, 184, 0.12);
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.terminal-status {
  font-weight: 600;
}

.terminal-status.idle {
  color: #94a3b8;
}

.terminal-status.pending {
  color: #fbbf24;
}

.terminal-status.success {
  color: #22c55e;
}

.terminal-status.failed {
  color: #f87171;
}

.status-banner {
  border-radius: 14px;
  padding: 12px 16px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(15, 23, 42, 0.5);
  display: grid;
  gap: 6px;
}

.status-banner.pending {
  border-color: rgba(59, 130, 246, 0.4);
}

.status-banner.success {
  border-color: rgba(34, 197, 94, 0.4);
}

.status-banner.failed {
  border-color: rgba(239, 68, 68, 0.4);
}

.status-title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.status-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}

.status-actions {
  display: flex;
  justify-content: flex-end;
}

.scan-aside {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.aside-section {
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(2, 6, 23, 0.5);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
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
}

@media (max-width: 640px) {
  .scan-view__header h2 {
    font-size: 22px;
  }

  .scan-meta {
    grid-template-columns: 1fr;
  }
}
</style>
