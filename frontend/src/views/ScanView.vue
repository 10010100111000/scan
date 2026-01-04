<template>
  <div class="scan-page">
    <header class="scan-page__header">
      <div>
        <p class="text-faint">扫描工作台 · ProjectDiscovery 风格</p>
        <h2 class="hero-title">创建项目、资产并触发扫描</h2>
      </div>
      <div class="actions">
        <el-button type="primary" @click="openSheet">Create</el-button>
        <el-button text @click="goDashboard">返回 Dashboard</el-button>
      </div>
    </header>

    <section class="scan-grid">
      <div class="rail-left card-glass">
        <div class="rail-title">项目与资产</div>
        <div class="rail-block">
          <p class="text-faint">当前项目 ID</p>
          <div class="highlight">{{ projectIdDisplay }}</div>
        </div>
        <div class="rail-block" v-if="lastAsset">
          <p class="text-faint">最近创建的资产</p>
          <div class="highlight">{{ lastAsset.name }} · {{ lastAsset.type }}</div>
        </div>
        <div class="rail-block">
          <el-button type="success" plain class="full" @click="openSheet">+ 新建扫描流程</el-button>
        </div>
      </div>

      <div class="main card-glass">
        <div class="section-head">
          <div>
            <p class="text-faint">任务流</p>
            <h3>最新扫描任务</h3>
          </div>
          <el-button link type="primary" @click="fetchTasks">刷新</el-button>
        </div>
        <el-empty v-if="tasks.length === 0" description="暂无任务，点击右上角 Create 开始" />
        <el-timeline v-else>
          <el-timeline-item
            v-for="task in tasks"
            :key="task.id"
            :timestamp="formatTime(task.created_at)"
            placement="top"
            :type="statusType(task.status)"
          >
            <div class="task-card">
              <div class="task-card__row">
                <strong>#{{ task.id }}</strong>
                <el-tag :type="statusTag(task.status)" effect="dark">{{ task.status }}</el-tag>
              </div>
              <div class="task-card__row">
                <span>配置：{{ task.config_name }}</span>
                <span>资产 ID：{{ task.asset_id ?? '—' }}</span>
              </div>
              <div class="task-card__row text-faint">
                <span>创建于 {{ formatTime(task.created_at) }}</span>
                <span v-if="task.completed_at">完成于 {{ formatTime(task.completed_at) }}</span>
              </div>
              <div v-if="task.log" class="task-log">{{ task.log }}</div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>

      <div class="rail-right card-glass">
        <div class="rail-title">扫描配置</div>
        <div class="config-list">
          <el-empty v-if="scanConfigs.length === 0" description="未加载" />
          <el-card v-for="cfg in scanConfigs" :key="cfg.name" class="config-card" shadow="never">
            <div class="config-card__title">{{ cfg.name }}</div>
            <p class="text-faint">{{ cfg.description || '无描述' }}</p>
            <el-tag size="small" type="info">{{ cfg.agent_type || 'unknown' }}</el-tag>
          </el-card>
        </div>
      </div>
    </section>

    <el-drawer v-model="sheetVisible" direction="btt" size="80%" :with-header="false" class="sheet">
      <div class="sheet__header">
        <div>
          <p class="text-faint">逐步完成：项目 → 资产 → 扫描</p>
          <h3>创建扫描任务</h3>
        </div>
        <el-button text @click="sheetVisible = false">关闭</el-button>
      </div>

      <div class="sheet__grid">
        <el-card shadow="never" class="step-card">
          <div class="step-card__header">
            <span class="bubble">1</span>
            <div>
              <p class="text-faint">创建项目</p>
              <strong>先有项目，才能挂资产</strong>
            </div>
          </div>
          <el-form :model="projectForm" label-width="100px" @submit.prevent>
            <el-form-item label="选择项目">
              <el-select
                v-model="currentProjectId"
                filterable
                remote
                clearable
                placeholder="搜索或选择已有项目"
                :remote-method="searchProjects"
                :loading="projectListLoading"
                @change="handleProjectSelect"
              >
                <el-option
                  v-for="proj in projectOptions"
                  :key="proj.id"
                  :label="proj.name"
                  :value="proj.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="项目名">
              <el-input v-model="projectForm.name" placeholder="如: security-lab" />
            </el-form-item>
            <el-button type="primary" :loading="projectLoading" @click="handleCreateProject">创建项目</el-button>
          </el-form>
        </el-card>

        <el-card shadow="never" class="step-card">
          <div class="step-card__header">
            <span class="bubble">2</span>
            <div>
              <p class="text-faint">添加根资产</p>
              <strong>域名或 CIDR，必填</strong>
            </div>
          </div>
          <el-form :model="assetForm" label-width="100px" @submit.prevent>
            <el-form-item label="选择资产">
              <el-select
                v-model="currentAssetId"
                :disabled="!currentProjectId"
                filterable
                remote
                clearable
                placeholder="搜索当前项目下资产"
                :remote-method="searchAssets"
                :loading="assetListLoading"
              >
                <el-option
                  v-for="asset in assetOptions"
                  :key="asset.id"
                  :label="`${asset.name} · ${asset.type}`"
                  :value="asset.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="资产类型">
              <el-select v-model="assetForm.type" placeholder="选择类型">
                <el-option label="域名" value="domain" />
                <el-option label="CIDR" value="cidr" />
              </el-select>
            </el-form-item>
            <el-form-item label="资产值">
              <el-input v-model="assetForm.name" placeholder="example.com 或 1.2.3.0/24" />
            </el-form-item>
            <el-button type="primary" :disabled="!currentProjectId" :loading="assetLoading" @click="handleCreateAsset">
              创建资产
            </el-button>
            <p class="text-faint inline-tip">当前项目 ID：{{ currentProjectId ?? '未选择' }}</p>
          </el-form>
        </el-card>

        <el-card shadow="never" class="step-card">
          <div class="step-card__header">
            <span class="bubble">3</span>
            <div>
              <p class="text-faint">选择扫描配置</p>
              <strong>基于 scanners.yaml 可用项</strong>
            </div>
          </div>
          <el-form :model="scanForm" label-width="120px" @submit.prevent>
            <el-form-item label="扫描配置">
              <el-select v-model="scanForm.config_name" filterable placeholder="选择配置">
                <el-option v-for="cfg in scanConfigs" :key="cfg.name" :label="cfg.name" :value="cfg.name">
                  <div class="option-row">
                    <strong>{{ cfg.name }}</strong>
                    <span class="text-faint">{{ cfg.description }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
            <el-button type="primary" :disabled="!currentAssetId || !scanForm.config_name" :loading="scanLoading" @click="handleTriggerScan">
              提交扫描
            </el-button>
            <p class="text-faint inline-tip">资产 ID：{{ currentAssetId ?? '未创建' }}</p>
          </el-form>
        </el-card>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import {
  fetchScanConfigs,
  listProjects,
  listAssets,
  createProject,
  createAsset,
  triggerScan,
  listTasks,
  type Asset,
  type ScanTask,
  type Project,
  type ScanConfigSummary,
} from '@/api/scan'

const router = useRouter()

const sheetVisible = ref(false)
const scanConfigs = ref<ScanConfigSummary[]>([])
const tasks = ref<ScanTask[]>([])

const currentProjectId = ref<number | null>(null)
const currentAssetId = ref<number | null>(null)
const lastAsset = ref<Asset | null>(null)
const projectOptions = ref<Project[]>([])
const assetOptions = ref<Asset[]>([])

const projectForm = reactive({ name: '' })
const assetForm = reactive<{ name: string; type: 'domain' | 'cidr' | '' }>({ name: '', type: '' })
const scanForm = reactive<{ config_name: string | '' }>({ config_name: '' })

const projectLoading = ref(false)
const assetLoading = ref(false)
const scanLoading = ref(false)
const projectListLoading = ref(false)
const assetListLoading = ref(false)

const projectIdDisplay = computed(() => currentProjectId.value ?? '未选择')

const openSheet = () => {
  sheetVisible.value = true
}

const goDashboard = () => router.push({ name: 'Dashboard' })

const loadConfigs = async () => {
  try {
    scanConfigs.value = await fetchScanConfigs()
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

const loadProjects = async (search = '') => {
  projectListLoading.value = true
  try {
    projectOptions.value = await listProjects({ limit: 20, search })
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    projectListLoading.value = false
  }
}

const searchProjects = async (query: string) => {
  await loadProjects(query)
}

const loadAssets = async (projectId: number, search = '') => {
  assetListLoading.value = true
  try {
    assetOptions.value = await listAssets(projectId, { limit: 50, search })
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    assetListLoading.value = false
  }
}

const searchAssets = async (query: string) => {
  if (!currentProjectId.value) return
  await loadAssets(currentProjectId.value, query)
}

const fetchTasks = async () => {
  try {
    tasks.value = await listTasks({ limit: 8 })
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

const handleCreateProject = async () => {
  if (!projectForm.name) {
    ElMessage.warning('请输入项目名或选择已有项目')
    return
  }
  projectLoading.value = true
  try {
    const project = await createProject({ name: projectForm.name })
    currentProjectId.value = project.id
    await loadProjects()
    ElMessage.success(`项目已创建：${project.name}`)
    await loadAssets(project.id)
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    projectLoading.value = false
  }
}

const handleProjectSelect = async () => {
  assetOptions.value = []
  currentAssetId.value = null
  lastAsset.value = null
  if (currentProjectId.value) {
    await loadAssets(currentProjectId.value)
  }
}

const handleCreateAsset = async () => {
  if (!currentProjectId.value) {
    ElMessage.warning('请先创建或选择项目')
    return
  }
  if (!assetForm.name || !assetForm.type) {
    ElMessage.warning('请填写资产类型和名称')
    return
  }
  assetLoading.value = true
  try {
    const asset = await createAsset(currentProjectId.value, {
      name: assetForm.name,
      type: assetForm.type as 'domain' | 'cidr',
    })
    currentAssetId.value = asset.id
    lastAsset.value = asset
    await loadAssets(currentProjectId.value)
    ElMessage.success(`资产已创建：${asset.name}`)
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    assetLoading.value = false
  }
}

const handleTriggerScan = async () => {
  if (!currentAssetId.value) {
    ElMessage.warning('请先创建资产')
    return
  }
  if (!scanForm.config_name) {
    ElMessage.warning('请选择扫描配置')
    return
  }
  scanLoading.value = true
  try {
    const task = await triggerScan(currentAssetId.value, { config_name: scanForm.config_name })
    ElMessage.success(`任务 #${task.id} 已创建`)
    await fetchTasks()
    sheetVisible.value = false
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    scanLoading.value = false
  }
}

const statusType = (status: ScanTask['status']) => {
  switch (status) {
    case 'running':
      return 'primary'
    case 'completed':
      return 'success'
    case 'failed':
      return 'danger'
    default:
      return 'info'
  }
}

const statusTag = (status: ScanTask['status']) => {
  switch (status) {
    case 'running':
      return 'primary'
    case 'completed':
      return 'success'
    case 'failed':
      return 'danger'
    default:
      return 'info'
  }
}

const formatTime = (v?: string | null) => (v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '—')

onMounted(async () => {
  await loadProjects()
  await loadConfigs()
  await fetchTasks()
})
</script>

<style scoped>
.scan-page {
  padding: 24px;
  color: #e2e8f0;
  min-height: 100vh;
  background: radial-gradient(circle at 15% 20%, rgba(64, 158, 255, 0.08), transparent 40%),
    radial-gradient(circle at 85% 10%, rgba(103, 194, 58, 0.08), transparent 35%),
    #0d1220;
}

.scan-page__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.actions {
  display: flex;
  gap: 12px;
}

.scan-grid {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  gap: 16px;
}

.card-glass {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

.rail-left,
.rail-right,
.main {
  padding: 16px;
}

.rail-title {
  font-weight: 700;
  margin-bottom: 12px;
}

.rail-block {
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.rail-block:last-child {
  border-bottom: none;
}

.highlight {
  font-size: 16px;
  font-weight: 700;
  margin-top: 4px;
}

.full {
  width: 100%;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.task-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 10px 12px;
}

.task-card__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.task-log {
  margin-top: 6px;
  font-size: 12px;
  color: #cbd5e1;
  max-height: 120px;
  overflow: auto;
  background: rgba(255, 255, 255, 0.03);
  padding: 8px;
  border-radius: 8px;
}

.config-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.config-card {
  background: rgba(255, 255, 255, 0.03);
}

.config-card__title {
  font-weight: 700;
  margin-bottom: 4px;
}

.sheet {
  background: rgba(12, 16, 26, 0.96);
  backdrop-filter: blur(10px);
}

.sheet__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.sheet__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
  padding-top: 12px;
}

.step-card {
  background: rgba(255, 255, 255, 0.02);
}

.step-card__header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.bubble {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #66b1ff, #67c23a);
  color: #0f172a;
  font-weight: 700;
}

.inline-tip {
  margin-top: 8px;
}

.option-row {
  display: flex;
  flex-direction: column;
}

@media (max-width: 1100px) {
  .scan-grid {
    grid-template-columns: 1fr;
  }
  .rail-left,
  .rail-right {
    order: 2;
  }
  .main {
    order: 1;
  }
}
</style>
