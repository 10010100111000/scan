<template>
  <section class="task-detail-view">
    <header class="task-detail-header card-glass">
      <div>
        <p class="text-faint">任务详情</p>
        <h2 class="hero-title">任务 #{{ taskDetail.id }}</h2>
        <p class="text-faint">策略执行与日志追踪</p>
      </div>
      <div class="task-detail-actions">
        <el-tag size="small" :type="statusTag(taskDetail.status)" effect="dark">{{ taskDetail.status }}</el-tag>
        <el-button size="small" text @click="refresh">刷新</el-button>
      </div>
    </header>

    <section class="task-detail-grid">
      <div class="card-glass info-card">
        <h3>基础信息</h3>
        <div class="info-grid">
          <div class="info-item">
            <span class="text-faint">任务 ID</span>
            <strong>{{ taskDetail.id }}</strong>
          </div>
          <div class="info-item">
            <span class="text-faint">配置 / 策略</span>
            <strong>{{ taskDetail.strategyName }}</strong>
          </div>
          <div class="info-item">
            <span class="text-faint">状态</span>
            <strong>{{ taskDetail.status }}</strong>
          </div>
          <div class="info-item">
            <span class="text-faint">创建时间</span>
            <strong>{{ taskDetail.createdAt }}</strong>
          </div>
          <div class="info-item">
            <span class="text-faint">完成时间</span>
            <strong>{{ taskDetail.completedAt || '-' }}</strong>
          </div>
          <div class="info-item">
            <span class="text-faint">项目</span>
            <strong>{{ taskDetail.project }}</strong>
          </div>
        </div>
      </div>

      <div class="card-glass steps-card">
        <h3>策略步骤</h3>
        <el-timeline>
          <el-timeline-item
            v-for="step in taskDetail.steps"
            :key="step.name"
            :timestamp="step.time"
            :type="step.type"
          >
            <div class="step-item">
              <strong>{{ step.name }}</strong>
              <p class="text-faint">{{ step.detail }}</p>
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>

      <div class="card-glass logs-card">
        <h3>日志</h3>
        <el-collapse v-model="activePanels">
          <el-collapse-item name="log">
            <template #title>
              <span>任务执行日志</span>
            </template>
            <el-scrollbar max-height="240px">
              <pre class="log-content">{{ taskDetail.log }}</pre>
            </el-scrollbar>
          </el-collapse-item>
        </el-collapse>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activePanels = ref(['log'])

const mockTasks = [
  {
    id: 1,
    strategyName: 'Web 扫描策略',
    status: '进行中',
    createdAt: '2024-05-28 14:08',
    completedAt: '',
    project: '电商平台',
    steps: [
      { name: '初始化配置', time: '14:08', type: 'primary', detail: '加载扫描配置并检查资产权限。' },
      { name: '执行扫描', time: '14:12', type: 'success', detail: '任务执行中，持续收集漏洞结果。' },
      { name: '写入结果', time: '待完成', type: 'info', detail: '等待扫描完成后整理报告。' },
    ],
    log: `14:08:05 初始化扫描配置\n14:08:08 连接资产 api.cloud.example\n14:09:12 发现 3 个子域\n14:12:41 执行端口扫描\n14:14:03 发现 2 个高危风险\n`,
  },
  {
    id: 2,
    strategyName: '端口巡检策略',
    status: '排队中',
    createdAt: '2024-05-28 13:42',
    completedAt: '',
    project: '基础设施',
    steps: [
      { name: '初始化配置', time: '13:42', type: 'primary', detail: '预检目标资产与扫描窗口。' },
      { name: '执行扫描', time: '待开始', type: 'info', detail: '等待资源空闲后执行。' },
      { name: '写入结果', time: '待开始', type: 'info', detail: '结果生成后进行资产关联。' },
    ],
    log: `13:42:11 已进入队列，等待执行。\n`,
  },
]

const taskDetail = computed(() => {
  const taskId = Number(route.params.id)
  return (
    mockTasks.find((task) => task.id === taskId) || {
      id: taskId,
      strategyName: '未知策略',
      status: '未知',
      createdAt: '- ',
      completedAt: '',
      project: '-',
      steps: [
        { name: '初始化配置', time: '-', type: 'info', detail: '等待任务初始化。' },
        { name: '执行扫描', time: '-', type: 'info', detail: '等待任务执行。' },
        { name: '写入结果', time: '-', type: 'info', detail: '等待结果写入。' },
      ],
      log: '暂无日志。',
    }
  )
})

const statusTag = (status: string) => {
  switch (status) {
    case '进行中':
      return 'success'
    case '排队中':
      return 'warning'
    case '失败':
      return 'danger'
    case '已完成':
      return 'info'
    default:
      return 'info'
  }
}

const refresh = () => {
  console.info('refresh task detail')
}
</script>

<style scoped>
.task-detail-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  width: 100%;
}

.task-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 16px;
}

.task-detail-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.info-card,
.steps-card,
.logs-card {
  padding: 20px;
  border-radius: 16px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
  margin-top: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.steps-card :deep(.el-timeline) {
  margin-top: 12px;
}

.step-item {
  display: grid;
  gap: 4px;
}

.logs-card :deep(.el-collapse) {
  margin-top: 12px;
}

.log-content {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: #e2e8f0;
  white-space: pre-wrap;
  padding: 12px 0;
}
</style>
