import { computed, onMounted, onUnmounted, ref } from 'vue'
import type { ScanTask } from '@/api/scan'

type IndicatorState = 'idle' | 'running' | 'completed' | 'failed'

const tasks = ref<ScanTask[]>([])
const indicator = ref<IndicatorState>('idle')
let eventSource: EventSource | null = null
let reconnectTimer: number | null = null
let lastErrorStatus: number | null = null

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

const parseMessage = (raw: string) => {
  try {
    return JSON.parse(raw) as { type?: string; data?: { tasks?: ScanTask[] } }
  } catch {
    return null
  }
}

const startStream = () => {
  if (eventSource) {
    return
  }
  const url = `/api/tasks/stream?limit=50`
  eventSource = new EventSource(url)
  eventSource.onmessage = (event) => {
    const message = parseMessage(event.data)
    if (!message || message.type !== 'task_status') {
      return
    }
    tasks.value = message.data?.tasks ?? []
    lastErrorStatus = null
    refreshIndicator()
  }
  eventSource.onerror = () => {
    lastErrorStatus = 0
    closeStream()
    scheduleReconnect()
  }
}

const closeStream = () => {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

const scheduleReconnect = () => {
  if (reconnectTimer) {
    return
  }
  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null
    startStream()
  }, 10000)
}

export const useTaskStatus = () => {
  onMounted(() => {
    startStream()
  })

  onUnmounted(() => {
    closeStream()
    if (reconnectTimer) {
      window.clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  })

  return {
    tasks,
    indicator: computed(() => indicator.value),
    lastErrorStatus: computed(() => lastErrorStatus),
  }
}
