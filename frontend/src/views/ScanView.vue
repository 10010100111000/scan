<template>
  <div class="scan-view">
    <header class="scan-view__header">
      <div>
        <p class="eyebrow">NEW SCAN</p>
        <h2>Launch a scan</h2>
        <p class="subtitle">Search a target and pick a scan profile to start.</p>
      </div>
    </header>

    <section class="scan-view__body">
      <div class="scan-panel card-glass">
        <div class="search-box">
          <el-input
            v-model="form.target"
            size="large"
            clearable
            placeholder="Search domain, host, or CIDR"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <div class="form-grid">
          <div class="field">
            <label class="field-label">Scan profile</label>
            <el-select v-model="form.config_name" filterable placeholder="Select a scan profile" class="full-width">
              <el-option v-for="cfg in scanConfigs" :key="cfg.name" :label="cfg.name" :value="cfg.name">
                <div class="option-row">
                  <strong>{{ cfg.name }}</strong>
                  <span class="text-faint">{{ cfg.description || 'No description' }}</span>
                </div>
              </el-option>
            </el-select>
          </div>
          <div class="field">
            <label class="field-label">Target type</label>
            <el-select v-model="form.asset_type" placeholder="Select type" class="full-width">
              <el-option label="Domain" value="domain" />
              <el-option label="CIDR" value="cidr" />
            </el-select>
          </div>
        </div>

        <div class="actions">
          <el-button
            type="primary"
            size="large"
            :loading="scanLoading"
            :disabled="!form.target || !form.config_name"
            @click="handleStartScan"
          >
            Start scan
          </el-button>
          <el-button text @click="resetForm">Reset</el-button>
        </div>

        <div class="scan-meta">
          <div>
            <p class="text-faint">Project</p>
            <strong>{{ projectLabel }}</strong>
          </div>
          <div v-if="lastTask">
            <p class="text-faint">Last task</p>
            <strong>#{{ lastTask.id }} · {{ lastTask.status }}</strong>
          </div>
        </div>
      </div>

      <aside class="scan-aside card-glass">
        <h3>Quick tips</h3>
        <ul>
          <li>Use a domain when scanning web services.</li>
          <li>Choose CIDR for network-wide discovery.</li>
          <li>Profiles are loaded from your backend config.</li>
        </ul>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import {
  createAsset,
  createProject,
  fetchScanConfigs,
  triggerScan,
  type ScanConfigSummary,
  type ScanTask,
} from '@/api/scan'

const scanConfigs = ref<ScanConfigSummary[]>([])
const scanLoading = ref(false)
const projectId = ref<number | null>(null)
const lastTask = ref<ScanTask | null>(null)

const form = reactive<{ target: string; config_name: string; asset_type: 'domain' | 'cidr' }>({
  target: '',
  config_name: '',
  asset_type: 'domain',
})

const projectLabel = computed(() => (projectId.value ? `#${projectId.value}` : 'Auto'))

const loadConfigs = async () => {
  try {
    scanConfigs.value = await fetchScanConfigs()
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

const ensureProjectId = async () => {
  if (projectId.value) {
    return projectId.value
  }
  const name = form.target.trim() ? `Scan ${form.target.trim()}` : 'Quick Scan'
  const project = await createProject({ name })
  projectId.value = project.id
  return project.id
}

const handleStartScan = async () => {
  const target = form.target.trim()
  if (!target) {
    ElMessage.warning('Enter a target to scan')
    return
  }
  if (!form.config_name) {
    ElMessage.warning('Select a scan profile')
    return
  }
  scanLoading.value = true
  try {
    const project = await ensureProjectId()
    const asset = await createAsset(project, { name: target, type: form.asset_type })
    const task = await triggerScan(asset.id, { config_name: form.config_name })
    lastTask.value = task
    ElMessage.success(`Task #${task.id} created`)
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    scanLoading.value = false
  }
}

const resetForm = () => {
  form.target = ''
  form.config_name = ''
  form.asset_type = 'domain'
}

onMounted(async () => {
  await loadConfigs()
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

.scan-aside {
  padding: 20px;
}

.scan-aside h3 {
  margin: 0 0 12px;
}

.scan-aside ul {
  margin: 0;
  padding-left: 18px;
  color: #cbd5e1;
  line-height: 1.6;
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
