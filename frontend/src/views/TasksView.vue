<template>
  <section class="tasks-view">
    <header class="tasks-header card-glass">
      <div>
        <p class="text-faint">Workflow</p>
        <h2 class="hero-title">Tasks</h2>
        <p class="text-faint">Monitor scans, retries, and alerts without leaving the rail layout.</p>
      </div>
      <div class="tasks-actions">
        <el-input v-model="query" size="small" clearable placeholder="Search task or target" />
        <el-select v-model="statusFilter" size="small" placeholder="Status">
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
          <el-button text size="small">{{ collapsed[group.key] ? 'Expand' : 'Collapse' }}</el-button>
        </div>
        <div v-if="!collapsed[group.key]" class="group-body">
          <div v-for="task in group.items" :key="task.id" class="task-row">
            <div>
              <strong>{{ task.name }}</strong>
              <p class="text-faint">{{ task.target }} · {{ task.owner }}</p>
            </div>
            <div class="task-meta">
              <el-tag size="small" :type="statusTag(task.status)" effect="dark">{{ task.status }}</el-tag>
              <span class="text-faint">{{ task.updated }}</span>
            </div>
          </div>
          <div v-if="group.items.length === 0" class="empty-row">
            <el-empty description="No tasks yet." />
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
  status: 'Running' | 'Queued' | 'Failed' | 'Completed'
  updated: string
}

const query = ref('')
const statusFilter = ref('All')
const statusOptions = ['All', 'Running', 'Queued', 'Failed', 'Completed']

const tasks = ref<TaskItem[]>([
  { id: 1, name: 'Web scan', target: 'api.cloud.example', owner: 'Blue Team', status: 'Running', updated: '2m ago' },
  { id: 2, name: 'Port sweep', target: 'jump.dev.lab', owner: 'Scheduler', status: 'Queued', updated: '4m ago' },
  { id: 3, name: 'Asset discovery', target: 'corp.example', owner: 'Scheduler', status: 'Completed', updated: '12m ago' },
  { id: 4, name: 'Credential check', target: 'vpn.example', owner: 'Red Team', status: 'Failed', updated: '32m ago' },
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
    const matchesStatus = status === 'All' || task.status === status
    return matchesQuery && matchesStatus
  })

  return [
    { key: 'running', title: 'Running', items: filtered.filter((task) => task.status === 'Running') },
    { key: 'queued', title: 'Queued', items: filtered.filter((task) => task.status === 'Queued') },
    { key: 'failed', title: 'Failed', items: filtered.filter((task) => task.status === 'Failed') },
    { key: 'completed', title: 'Completed', items: filtered.filter((task) => task.status === 'Completed') },
  ]
})

const toggleGroup = (key: string) => {
  collapsed[key] = !collapsed[key]
}

const statusTag = (status: TaskItem['status']) => {
  switch (status) {
    case 'Running':
      return 'success'
    case 'Queued':
      return 'warning'
    case 'Failed':
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

.empty-row {
  padding: 12px;
}
</style>
