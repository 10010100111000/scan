<template>
  <section class="tasks-view">
    <header class="tasks-header card-glass">
      <div>
        <p class="text-faint">任务中心</p>
        <h2 class="hero-title">扫描任务</h2>
        <p class="text-faint">集中查看任务状态、策略与归档项目。</p>
      </div>
      <div class="tasks-actions">
        <el-input v-model="query" size="small" clearable placeholder="搜索任务或配置" />
        <el-select v-model="statusFilter" size="small" placeholder="状态">
          <el-option v-for="status in statusOptions" :key="status.value" :label="status.label" :value="status.value" />
        </el-select>
        <el-select v-model="projectFilter" size="small" placeholder="项目">
          <el-option v-for="project in projectOptions" :key="project.value" :label="project.label" :value="project.value" />
        </el-select>
        <el-button text size="small" :loading="loading" @click="refreshTasks">刷新</el-button>
      </div>
    </header>

    <section class="tasks-body">
      <div class="card-glass task-list-card">
        <div class="task-list-header">
          <div>
            <strong>任务列表</strong>
            <span class="text-faint">共 {{ total }} 条</span>
          </div>
          <div class="text-faint">最近 {{ tasks.length }} 条</div>
        </div>
        <div class="task-table">
          <div v-if="tasks.length === 0" class="empty-row">
            <el-empty description="暂无任务" />
          </div>
          <div v-for="task in tasks" :key="task.id" class="task-row" @click="openDetail(task)">
            <div class="task-main">
              <strong>#{{ task.id }}</strong>
              <span class="text-faint"> · {{ task.config_name }}</span>
            </div>
            <div class="task-meta">
              <el-tag size="small" :type="statusTag(task.status)" effect="dark">{{ task.status }}</el-tag>
              <span class="text-faint">项目 {{ task.project_name ?? '默认' }}</span>
              <span class="text-faint">{{ formatTime(task.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <aside class="card-glass task-detail-card">
        <div class="detail-header">
          <div>
            <h3>任务详情</h3>
            <p class="text-faint">点击列表查看任务日志与结果入口</p>
          </div>
        </div>
        <div v-if="selectedTask === null" class="text-faint">请选择任务</div>
        <div v-else class="detail-body">
          <div class="detail-row">
            <span class="text-faint">任务 ID</span>
            <strong>#{{ selectedTask.id }}</strong>
          </div>
          <div class="detail-row">
            <span class="text-faint">配置</span>
            <strong>{{ selectedTask.config_name }}</strong>
          </div>
          <div class="detail-row">
            <span class="text-faint">资产</span>
            <strong>{{ selectedTask.asset_id ?? 'N/A' }}</strong>
          </div>
          <div class="detail-row">
            <span class="text-faint">项目</span>
            <strong>{{ selectedTask.project_name ?? '默认' }}</strong>
          </div>
          <div class="detail-row">
            <span class="text-faint">状态</span>
            <el-tag size="small" :type="statusTag(selectedTask.status)" effect="dark">
              {{ selectedTask.status }}
            </el-tag>
          </div>
          <div class="detail-row">
            <span class="text-faint">创建时间</span>
            <strong>{{ formatTime(selectedTask.created_at) }}</strong>
          </div>
          <div class="detail-row" v-if="selectedTask.completed_at">
            <span class="text-faint">完成时间</span>
            <strong>{{ formatTime(selectedTask.completed_at) }}</strong>
          </div>
          <div class="detail-section">
            <p class="text-faint">任务日志</p>
            <pre class="task-log">{{ selectedTask.log || '暂无日志' }}</pre>
          </div>
          <div class="detail-actions">
            <el-button size="small" @click="goToTaskDetail">查看详情</el-button>
            <el-button size="small" :disabled="!selectedTask.asset_id" @click="goToResultDetail">
              查看结果详情
            </el-button>
          </div>
        </div>
      </aside>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  fetchProjects,
  listTasks,
  type Project,
  type ScanTask,
} from '@/api/scan'

const router = useRouter()
const query = ref('')
const statusFilter = ref<string | null>(null)
const statusOptions = [
  { label: '全部', value: null },
  { label: '进行中', value: 'running' },
  { label: '排队中', value: 'pending' },
  { label: '失败', value: 'failed' },
  { label: '已完成', value: 'completed' },
]
const loading = ref(false)
const tasks = ref<ScanTask[]>([])
const total = ref(0)
const selectedTask = ref<ScanTask | null>(null)
const projectFilter = ref<number | null>(null)
const projectOptions = ref<{ label: string; value: number | null }[]>([{ label: '全部', value: null }])
const projectList = ref<Project[]>([])

const refreshTasks = async () => {
  loading.value = true
  try {
    const params: Record<string, unknown> = { limit: 50 }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    if (query.value.trim()) {
      params.config_name = query.value.trim()
    }
    if (projectFilter.value) {
      // 任务中心按项目筛选
      params.project_id = projectFilter.value
    }
    const data = await listTasks(params)
    tasks.value = data
    total.value = data.length
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    loading.value = false
  }
}

const loadProjects = async () => {
  try {
    projectList.value = await fetchProjects({ limit: 100 })
    projectOptions.value = [
      { label: '全部', value: null },
      ...projectList.value.map((project) => ({ label: project.name, value: project.id })),
    ]
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

const openDetail = (task: ScanTask) => {
  selectedTask.value = task
}

const goToResultDetail = () => {
  if (!selectedTask.value?.asset_id) {
    ElMessage.warning('当前任务没有可展示的结果')
    return
  }
  router.push({ name: 'Results', params: { assetId: selectedTask.value.asset_id } })
}

const goToTaskDetail = () => {
  if (!selectedTask.value) {
    ElMessage.warning('请先选择任务')
    return
  }
  router.push({ name: 'TaskDetail', params: { taskId: selectedTask.value.id } })
}

const statusTag = (status: ScanTask['status']) => {
  switch (status) {
    case 'running':
      return 'success'
    case 'pending':
      return 'warning'
    case 'failed':
      return 'danger'
    default:
      return 'info'
  }
}

const formatTime = (value?: string | null) => {
  if (!value) return 'N/A'
  return new Date(value).toLocaleString()
}

onMounted(() => {
  refreshTasks()
  loadProjects()
})

watch([statusFilter, projectFilter], () => {
  refreshTasks()
})

watch(query, () => {
  const keyword = query.value.trim()
  if (keyword.length === 0 || keyword.length >= 2) {
    refreshTasks()
  }
})
</script>

<style scoped>
.tasks-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  width: 100%;
}

.tasks-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 16px;
}

.tasks-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tasks-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
}

.task-list-card {
  padding: 16px;
  border-radius: 16px;
}

.task-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.task-table {
  display: grid;
  gap: 12px;
}

.task-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.empty-row {
  padding: 12px;
}

.task-detail-card {
  padding: 16px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-header h3 {
  margin: 0;
}

.detail-body {
  display: grid;
  gap: 10px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.detail-section {
  background: rgba(15, 23, 42, 0.55);
  padding: 8px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.task-log {
  margin: 6px 0 0;
  white-space: pre-wrap;
  font-size: 12px;
}

.detail-actions {
  display: flex;
  gap: 8px;
}

@media (max-width: 1100px) {
  .tasks-body {
    grid-template-columns: 1fr;
  }
}
</style>
