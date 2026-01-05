<template>
  <section class="tasks-view">
    <header class="tasks-header card-glass">
      <div>
        <p class="text-faint">任务流</p>
        <h2 class="hero-title">任务</h2>
        <p class="text-faint">集中查看扫描、重试与告警。</p>
      </div>
      <div class="tasks-actions">
        <el-input v-model="query" size="small" clearable placeholder="搜索任务或目标" />
        <el-select v-model="statusFilter" size="small" placeholder="状态">
          <el-option v-for="status in statusOptions" :key="status" :label="status" :value="status" />
        </el-select>
      </div>
    </header>

    <section class="tasks-groups">
      <div v-for="group in filteredGroups" :key="group.key" class="card-glass group-card">
        <div class="group-header" @click="toggleGroup(group.key)">
          <div>
            <h3>{{ group.title }}</h3>
            <p class="text-faint">{{ group.items.length }} tasks</p>
          </div>
          <el-button text size="small">{{ collapsed[group.key] ? '展开' : '收起' }}</el-button>
        </div>
        <div v-if="!collapsed[group.key]" class="group-body">
          <div v-for="task in group.items" :key="task.id" class="task-row">
            <div>
              <strong>{{ task.name }}</strong>
              <p class="text-faint">{{ task.target }} · {{ task.owner }}</p>
            </div>
            <div class="task-meta">
              <div class="task-meta-info">
                <el-tag size="small" :type="statusTag(task.status)" effect="dark">{{ task.status }}</el-tag>
                <span class="text-faint">{{ task.updated }}</span>
              </div>
              <router-link :to="{ name: 'TaskDetail', params: { id: task.id } }">
                <el-button size="small" text>查看详情</el-button>
              </router-link>
            </div>
          </div>
          <div v-if="group.items.length === 0" class="empty-row">
            <el-empty description="暂无任务。" />
          </div>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

type TaskItem = {
  id: number
  name: string
  target: string
  owner: string
  status: '进行中' | '排队中' | '失败' | '已完成'
  updated: string
}

const query = ref('')
const statusFilter = ref('All')
const statusOptions = ['全部', '进行中', '排队中', '失败', '已完成']

const tasks = ref<TaskItem[]>([
  { id: 1, name: 'Web 扫描', target: 'api.cloud.example', owner: '蓝队', status: '进行中', updated: '2 分钟前' },
  { id: 2, name: '端口巡检', target: 'jump.dev.lab', owner: '调度器', status: '排队中', updated: '4 分钟前' },
  { id: 3, name: '资产发现', target: 'corp.example', owner: '调度器', status: '已完成', updated: '12 分钟前' },
  { id: 4, name: '口令检查', target: 'vpn.example', owner: '红队', status: '失败', updated: '32 分钟前' },
])

const collapsed = reactive<Record<string, boolean>>({
  running: false,
  queued: false,
  failed: false,
  completed: false,
})

const filteredGroups = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  const status = statusFilter.value
  const filtered = tasks.value.filter((task) => {
    const matchesQuery =
      !keyword ||
      task.name.toLowerCase().includes(keyword) ||
      task.target.toLowerCase().includes(keyword) ||
      task.owner.toLowerCase().includes(keyword)
    const matchesStatus = status === '全部' || task.status === status
    return matchesQuery && matchesStatus
  })

  return [
    { key: 'running', title: '进行中', items: filtered.filter((task) => task.status === '进行中') },
    { key: 'queued', title: '排队中', items: filtered.filter((task) => task.status === '排队中') },
    { key: 'failed', title: '失败', items: filtered.filter((task) => task.status === '失败') },
    { key: 'completed', title: '已完成', items: filtered.filter((task) => task.status === '已完成') },
  ]
})

const toggleGroup = (key: string) => {
  collapsed[key] = !collapsed[key]
}

const statusTag = (status: TaskItem['status']) => {
  switch (status) {
    case '进行中':
      return 'success'
    case '排队中':
      return 'warning'
    case '失败':
      return 'danger'
    default:
      return 'info'
  }
}
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

.tasks-groups {
  display: grid;
  gap: 16px;
}

.group-card {
  padding: 16px;
  border-radius: 16px;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.group-header h3 {
  margin: 0 0 4px;
}

.group-body {
  margin-top: 12px;
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
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-meta-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-meta :deep(.el-button) {
  padding: 0;
}

.empty-row {
  padding: 12px;
}
</style>
