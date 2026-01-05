import { computed, onMounted, onUnmounted, ref } from 'vue'
import { listTasks, type ScanTask } from '@/api/scan'

type IndicatorState = 'idle' | 'running' | 'completed' | 'failed'

const tasks = ref<ScanTask[]>([])
const indicator = ref<IndicatorState>('idle')
let pollTimer: number | null = null
let isPolling = false

const refreshIndicator = () => {
  if (tasks.value.length === 0) {
    indicator.value = 'idle'
    return
  }
  if (tasks.value.some((task) => task.status === 'failed')) {
    indicator.value = 'failed'
    return
  }
  if (tasks.value.some((task) => task.status === 'pending' || task.status === 'running')) {
    indicator.value = 'running'
    return
  }
  indicator.value = 'completed'
}

const fetchTaskList = async () => {
  const response = await listTasks({ limit: 50 })
  tasks.value = response
  refreshIndicator()
}

const startPolling = () => {
  if (isPolling) {
    return
  }
  isPolling = true
  pollTimer = window.setInterval(() => {
    fetchTaskList().catch(() => {
      // keep last state if polling fails
    })
  }, 6000)
}

const stopPolling = () => {
  if (pollTimer) {
    window.clearInterval(pollTimer)
    pollTimer = null
  }
  isPolling = false
}

export const useTaskStatus = () => {
  onMounted(() => {
    fetchTaskList().catch(() => {
      // ignore initial errors
    })
    startPolling()
  })

  onUnmounted(() => {
    stopPolling()
  })

  return {
    tasks,
    indicator: computed(() => indicator.value),
    refresh: fetchTaskList,
  }
}
