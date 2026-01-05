<template>
  <div class="scan-view">
    <header class="scan-view__header">
      <div>
        <p class="eyebrow">新建扫描</p>
        <h2>发起扫描任务</h2>
        <p class="subtitle">选择项目、目标与 Scan profile，任务会在后台执行。</p>
      </div>
    </header>

    <section class="scan-view__body">
      <div class="scan-panel card-glass">
        <div class="form-grid">
          <div class="field">
            <label class="field-label">项目</label>
            <el-select
              v-model="form.project_id"
              filterable
              remote
              clearable
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
            <label class="field-label">Scan profile</label>
            <el-select
              v-model="form.config_name"
              filterable
              placeholder="选择 Scan profile"
              class="full-width"
              :loading="scanConfigsLoading"
            >
              <el-option v-for="cfg in scanConfigs" :key="cfg.name" :label="cfg.name" :value="cfg.name">
                <div class="option-row">
                  <strong>{{ cfg.name }}</strong>
                  <span class="text-faint">{{ cfg.description || '暂无描述' }}</span>
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
            开始扫描
          </el-button>
          <el-button text @click="resetForm">重置</el-button>
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
          <li>Scan profile 来自后端配置 <code>scanners.yaml</code>。</li>
          <li>建议选择项目以便归类扫描结果。</li>
          <li>同名资产会直接复用，不重复发起任务。</li>
        </ul>
        <div class="aside-meta">
          <div>
            <p class="text-faint">可用配置</p>
            <strong>{{ scanConfigs.length }}</strong>
          </div>
          <div>
            <p class="text-faint">项目数量</p>
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
import { Search } from '@element-plus/icons-vue'
import {
  createAsset,
  createProject,
  fetchAssetsForProject,
  fetchProjects,
  fetchScanConfigs,
  searchAssetsByName,
  triggerScan,
  type Project,
  type ScanConfigSummary,
} from '@/api/scan'
import { useScanOverlay } from '@/composables/useScanOverlay'
const { close: closeScan } = useScanOverlay()

const scanConfigs = ref<ScanConfigSummary[]>([])
const scanConfigsLoading = ref(false)
const scanSubmitting = ref(false)

const projects = ref<Project[]>([])
const projectsLoading = ref(false)
const projectCreating = ref(false)
const newProjectName = ref('')
const currentTarget = ref('')
const terminalLines = ref<string[]>([])
const terminalStatus = ref<'idle' | 'pending' | 'success' | 'failed'>('idle')
let autoCloseTimer: number | null = null

const form = reactive<{
  target: string
  config_name: string
  project_id: number | null
}>({
  target: '',
  config_name: '',
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
  if (!form.config_name) {
    ElMessage.warning('请选择 Scan profile')
    return
  }
  scanSubmitting.value = true
  try {
    terminalLines.value = []
    terminalStatus.value = 'pending'
    if (autoCloseTimer) {
      window.clearTimeout(autoCloseTimer)
      autoCloseTimer = null
    }

    const existingAssets = await searchAssetsByName(normalizedTarget, 1)
    if (existingAssets.length > 0) {
      currentTarget.value = existingAssets[0].name
      form.project_id = existingAssets[0].project_id
      terminalLines.value.push('目标已存在，直接复用历史结果。')
      terminalStatus.value = 'success'
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
    const task = await triggerScan(assetId, { config_name: form.config_name })
    terminalLines.value.push(`任务 #${task.id} 已提交。`)
    terminalStatus.value = 'success'
    ElMessage.success(`任务 #${task.id} 已提交`)
    autoCloseTimer = window.setTimeout(() => {
      closeScan()
    }, 1800)
  } catch (error) {
    terminalLines.value.push(`推送失败：${(error as Error).message}`)
    terminalStatus.value = 'failed'
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
  if (autoCloseTimer) {
    window.clearTimeout(autoCloseTimer)
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
