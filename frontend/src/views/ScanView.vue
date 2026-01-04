<template>
  <div class="scan-view">
    <header class="scan-view__header">
      <div>
        <p class="eyebrow">????</p>
        <h2>??????</h2>
        <p class="subtitle">?????????????????????????</p>
      </div>
    </header>

    <section class="scan-view__body">
      <div class="scan-panel card-glass">
        <div class="form-grid">
          <div class="field">
            <label class="field-label">??</label>
            <el-select
              v-model="form.project_id"
              filterable
              remote
              clearable
              placeholder="???????"
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
              <el-button text size="small" @click="loadProjects">????</el-button>
            </div>
          </div>
          <div class="field">
            <label class="field-label">????????</label>
            <div class="inline-row">
              <el-input v-model="newProjectName" clearable placeholder="??????" />
              <el-button
                type="primary"
                plain
                :disabled="!newProjectName"
                :loading="projectCreating"
                @click="handleCreateProject"
              >
                ??
              </el-button>
            </div>
          </div>
        </div>

        <div class="search-box">
          <el-input v-model="form.target" size="large" clearable placeholder="???? / IP / CIDR">
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="form-grid">
          <div class="field">
            <label class="field-label">????</label>
            <el-select
              v-model="form.config_name"
              filterable
              placeholder="??????"
              class="full-width"
              :loading="scanConfigsLoading"
            >
              <el-option v-for="cfg in scanConfigs" :key="cfg.name" :label="cfg.name" :value="cfg.name">
                <div class="option-row">
                  <strong>{{ cfg.name }}</strong>
                  <span class="text-faint">{{ cfg.description || '????' }}</span>
                </div>
              </el-option>
            </el-select>
          </div>
          <div class="field">
            <label class="field-label">????</label>
            <el-select v-model="form.asset_type" placeholder="????" class="full-width">
              <el-option label="Domain" value="domain" />
              <el-option label="CIDR" value="cidr" />
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
            ????
          </el-button>
          <el-button text @click="resetForm">??</el-button>
        </div>

        <div class="scan-meta">
          <div>
            <p class="text-faint">????</p>
            <strong>{{ projectLabel }}</strong>
          </div>
          <div v-if="lastTask">
            <p class="text-faint">????</p>
            <strong>#{{ lastTask.id }} ? {{ lastTask.status }}</strong>
          </div>
        </div>

        <div v-if="scanRunning" class="scan-progress">
          <div class="scan-progress__ring">
            <el-icon class="is-loading"><Loading /></el-icon>
          </div>
          <h3>??????????</h3>
          <p class="text-faint">?? {{ lastTask?.id }} ??????????????</p>
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
          <el-button text :loading="scanStatusLoading" @click="refreshTaskStatus">??????</el-button>
        </div>
      </div>

      <aside class="scan-aside card-glass">
        <h3>??</h3>
        <ul>
          <li>???????? <code>scanners.yaml</code>?</li>
          <li>??????????????????</li>
          <li>???????????????</li>
        </ul>
        <div class="aside-meta">
          <div>
            <p class="text-faint">????</p>
            <strong>{{ scanConfigs.length }}</strong>
          </div>
          <div>
            <p class="text-faint">????</p>
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
import {
  createAsset,
  createProject,
  fetchAssetsForProject,
  fetchProjects,
  fetchScanConfigs,
  fetchTask,
  triggerScan,
  type Project,
  type ScanConfigSummary,
  type ScanTask,
} from '@/api/scan'

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
let pollTimer: number | null = null

const form = reactive<{
  target: string
  config_name: string
  asset_type: 'domain' | 'cidr'
  project_id: number | null
}>({
  target: '',
  config_name: '',
  asset_type: 'domain',
  project_id: null,
})

const progressSteps = ['??????', '????', '??????', '??']

const projectLabel = computed(() => {
  const project = projects.value.find((item) => item.id === form.project_id)
  if (project) {
    return `${project.name} (#${project.id})`
  }
  return '???'
})

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
    ElMessage.success(`??????${project.name}`)
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
    ElMessage.warning('????????')
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
  const existing = assets.find((asset) => asset.name === target)
  if (existing) {
    return existing.id
  }
  const asset = await createAsset(projectId, { name: target, type: form.asset_type })
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

const handleStartScan = async () => {
  const target = form.target.trim()
  if (!target) {
    ElMessage.warning('???????')
    return
  }
  if (!form.config_name) {
    ElMessage.warning('???????')
    return
  }
  scanSubmitting.value = true
  try {
    const projectId = await ensureProjectId()
    if (!projectId) {
      return
    }
    const assetId = await resolveAssetId(projectId, target)
    const task = await triggerScan(assetId, { config_name: form.config_name })
    lastTask.value = task
    scanRunning.value = task.status === 'pending' || task.status === 'running'
    ElMessage.success(`?? #${task.id} ???`)
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
  form.asset_type = 'domain'
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
  letter-spacing: 0.16em;
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
  display: flex;
  gap: 24px;
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
    flex-direction: column;
    gap: 10px;
  }
}
</style>
