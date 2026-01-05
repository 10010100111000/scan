<template>
  <section class="task-detail-view">
    <header class="task-header card-glass">
      <div>
        <p class="text-faint">任务中心</p>
        <h2 class="hero-title">任务详情</h2>
        <p class="text-faint">展示策略步骤与任务执行状态。</p>
      </div>
      <div class="header-actions">
        <el-button size="small" :loading="loading" @click="refreshTask">刷新</el-button>
        <el-button size="small" @click="goBack">返回任务中心</el-button>
      </div>
    </header>

    <section class="task-body">
      <div class="card-glass task-main">
        <div class="task-summary">
          <div>
            <h3>#{{ task?.id ?? '-' }} · {{ task?.config_name || '未加载' }}</h3>
            <p class="text-faint">{{ taskSubtitle }}</p>
          </div>
          <el-tag v-if="task" size="small" :type="statusTag(task.status)" effect="dark">
            {{ task.status }}
          </el-tag>
        </div>

        <div v-if="!task" class="empty-row">
          <el-empty description="暂无任务数据" />
        </div>

        <div v-else class="task-detail-grid">
          <div class="detail-item">
            <span class="text-faint">项目</span>
            <strong>{{ task.project_name ?? '默认' }}</strong>
          </div>
          <div class="detail-item">
            <span class="text-faint">资产</span>
            <strong>{{ task.asset_id ?? 'N/A' }}</strong>
          </div>
          <div class="detail-item">
            <span class="text-faint">创建时间</span>
            <strong>{{ formatTime(task.created_at) }}</strong>
          </div>
          <div class="detail-item">
            <span class="text-faint">完成时间</span>
            <strong>{{ formatTime(task.completed_at) }}</strong>
          </div>
        </div>

        <div v-if="task" class="step-section">
          <div class="section-title">
            <h4>策略步骤</h4>
            <span class="text-faint">{{ task.strategy_name || '未识别策略' }}</span>
          </div>
          <div class="step-list">
            <div v-for="step in stepStatuses" :key="step.config_name" class="step-item">
              <div>
                <strong>{{ step.config_name }}</strong>
                <p class="text-faint">{{ stepHint(step) }}</p>
                <p v-if="step.stage" class="text-faint">阶段：{{ step.stage }}</p>
              </div>
              <div class="step-actions">
                <el-tag size="small" :type="statusTag(step.status ?? 'pending')" effect="plain">
                  {{ step.status || 'pending' }}
                </el-tag>
                <el-button
                  v-if="step.task_id && step.artifact_path"
                  text
                  size="small"
                  @click="downloadArtifact(step.task_id)"
                >
                  下载产物
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="task" class="log-section">
          <div class="section-title">
            <h4>任务日志</h4>
          </div>
          <pre class="task-log">{{ task.log || '暂无日志' }}</pre>
        </div>
      </div>

      <aside class="card-glass task-aside">
        <h3>操作</h3>
        <div class="aside-actions">
          <el-button
            v-if="task?.status === 'completed'"
            type="primary"
            plain
            size="small"
            :disabled="!task?.asset_id"
            @click="goResult"
          >
            查看结果详情
          </el-button>
          <el-button
            v-if="task?.status === 'failed'"
            size="small"
            :loading="retryLoading"
            @click="handleRetry('step')"
          >
            重试当前步骤
          </el-button>
          <el-button
            v-if="task?.status === 'failed'"
            type="primary"
            plain
            size="small"
            :loading="retryLoading"
            @click="handleRetry('strategy')"
          >
            重新执行策略
          </el-button>
        </div>
        <p class="text-faint">
          失败任务可重试步骤或重跑策略；成功任务可查看资产结果详情。
        </p>
        <div class="aside-section">
          <p class="text-faint">当前步骤</p>
          <strong>{{ task?.current_step || '-' }}</strong>
        </div>
      </aside>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchTask, retryTask, type ScanTask, type ScanTaskStepStatus } from '@/api/scan'

const route = useRoute()
const router = useRouter()
const task = ref<ScanTask | null>(null)
const loading = ref(false)
const retryLoading = ref(false)

const taskId = computed(() => Number(route.params.taskId || 0))

const taskSubtitle = computed(() => {
  if (!task.value) return '请从任务中心进入'
  return `项目 ${task.value.project_name ?? '默认'} · 资产 ${task.value.asset_id ?? 'N/A'}`
})

const stepStatuses = computed<ScanTaskStepStatus[]>(() => {
  if (!task.value) return []
  if (task.value.step_statuses && task.value.step_statuses.length > 0) {
    return task.value.step_statuses
  }
  if (task.value.strategy_steps && task.value.strategy_steps.length > 0) {
    return task.value.strategy_steps.map((step) => ({ config_name: step, status: 'pending' }))
  }
  return [{ config_name: task.value.config_name, status: task.value.status }]
})

const refreshTask = async () => {
  if (!taskId.value) {
    task.value = null
    return
  }
  loading.value = true
  try {
    task.value = await fetchTask(taskId.value)
  } catch (error) {
    task.value = null
    ElMessage.error((error as Error).message)
  } finally {
    loading.value = false
  }
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

const stepHint = (step: ScanTaskStepStatus) => {
  if (task.value?.current_step === step.config_name) {
    return '当前执行步骤'
  }
  if (step.completed_at) {
    return `完成于 ${new Date(step.completed_at).toLocaleString()}`
  }
  return step.status === 'completed' ? '已完成' : '等待执行'
}

const downloadArtifact = (taskId: number) => {
  window.open(`/api/tasks/${taskId}/artifact`, '_blank')
}

const formatTime = (value?: string | null) => {
  if (!value) return 'N/A'
  return new Date(value).toLocaleString()
}

const goBack = () => {
  router.push({ name: 'Tasks' })
}

const goResult = () => {
  if (!task.value?.asset_id) {
    ElMessage.warning('当前任务没有可查看的结果')
    return
  }
  router.push({ name: 'Results', params: { assetId: task.value.asset_id } })
}

const handleRetry = async (mode: 'strategy' | 'step') => {
  if (!task.value) {
    ElMessage.warning('暂无可重试任务')
    return
  }
  retryLoading.value = true
  try {
    await retryTask(task.value.id, { mode })
    ElMessage.success(mode === 'step' ? '已触发步骤重试' : '已触发策略重试')
    await refreshTask()
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    retryLoading.value = false
  }
}

onMounted(() => {
  refreshTask()
})
</script>

<style scoped>
.task-detail-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  width: 100%;
}

.task-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 16px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.task-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 16px;
}

.task-main {
  padding: 16px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.task-detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.step-section {
  display: grid;
  gap: 12px;
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.step-list {
  display: grid;
  gap: 10px;
}

.step-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.step-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-section {
  display: grid;
  gap: 8px;
}

.task-log {
  margin: 0;
  white-space: pre-wrap;
  font-size: 12px;
  background: rgba(2, 6, 23, 0.55);
  border-radius: 12px;
  padding: 12px;
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.task-aside {
  padding: 16px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.aside-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.aside-section {
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(2, 6, 23, 0.5);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.empty-row {
  padding: 12px;
}

.text-faint {
  color: #94a3b8;
}

@media (max-width: 1100px) {
  .task-body {
    grid-template-columns: 1fr;
  }
}
</style>
