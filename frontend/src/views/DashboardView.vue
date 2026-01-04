<template>
  <section class="dashboard-main">
    <header class="dashboard-header card-glass">
      <div>
        <p class="text-faint">Welcome back</p>
        <h2 class="hero-title">Attack Surface Command Center</h2>
        <p class="text-faint header-hint">Monitor assets, orchestrate scans, and track exposures in one place.</p>
      </div>
      <div class="user-area">
        <div class="user-meta">
          <strong>{{ userInfo?.realName || userInfo?.username }}</strong>
          <span class="text-faint">{{ userInfo?.roles?.join(', ') || 'Visitor' }}</span>
        </div>
        <el-avatar :size="40" :src="userInfo?.avatar">
          {{ userInfo?.username?.slice(0, 1).toUpperCase() }}
        </el-avatar>
        <el-button size="small" type="danger" @click="handleLogout">Sign out</el-button>
      </div>
    </header>

    <section class="kpi-grid">
      <div v-for="kpi in kpiCards" :key="kpi.title" class="card-glass kpi-card">
        <div class="kpi-icon" :style="{ background: kpi.tint }">
          <el-icon><component :is="kpi.icon" /></el-icon>
        </div>
        <div class="kpi-content">
          <p class="text-faint">{{ kpi.title }}</p>
          <div class="kpi-value-row">
            <strong class="kpi-value">{{ kpi.value }}</strong>
            <el-tag :type="kpi.tagType" size="small" effect="dark">{{ kpi.caption }}</el-tag>
          </div>
          <p class="kpi-sub">{{ kpi.subTitle }}</p>
        </div>
      </div>
    </section>

    <section class="panel-grid">
      <div class="card-glass panel">
        <div class="panel-header">
          <div>
            <p class="text-faint">Ongoing tasks</p>
            <h3>Active scans</h3>
          </div>
          <el-button text type="primary" size="small" @click="goTasks">View all</el-button>
        </div>
        <div class="panel-body tasks">
          <div v-for="task in ongoingTasks" :key="task.name" class="task-item">
            <div class="task-meta">
              <h4>{{ task.name }}</h4>
              <p class="text-faint">{{ task.owner }} · ETA {{ task.eta }}</p>
            </div>
            <div class="task-progress">
              <el-progress :percentage="task.progress" :status="task.status === 'paused' ? 'warning' : 'success'" :stroke-width="10" />
              <div class="task-tags">
                <el-tag size="small" effect="plain">{{ task.stream }}</el-tag>
                <el-tag v-if="task.status === 'paused'" size="small" type="warning" effect="plain">Paused</el-tag>
                <el-tag v-else size="small" type="success" effect="plain">Running</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="card-glass panel">
        <div class="panel-header">
          <div>
            <p class="text-faint">Asset preview</p>
            <h3>Latest assets</h3>
          </div>
          <el-button text type="primary" size="small">Export</el-button>
        </div>
        <div class="panel-body asset-table">
          <el-table :data="assetsPreview" size="small" border stripe>
            <el-table-column prop="name" label="Asset" min-width="140" />
            <el-table-column prop="ip" label="IP / Domain" min-width="140" />
            <el-table-column label="Tags" min-width="160">
              <template #default="{ row }">
                <div class="tag-row">
                  <el-tag v-for="tag in row.tags" :key="tag" size="small" effect="plain">{{ tag }}</el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="Status" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'Online' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </section>

    <section class="panel-grid lower">
      <div class="card-glass panel findings">
        <div class="panel-header">
          <div>
            <p class="text-faint">Latest findings</p>
            <h3>Recent exposure</h3>
          </div>
          <el-button text type="primary" size="small">Export report</el-button>
        </div>
        <div class="panel-body findings-list">
          <div v-for="finding in findings" :key="finding.title" class="finding-item">
            <div class="finding-severity" :class="finding.level">
              <el-icon><WarningFilled /></el-icon>
            </div>
            <div class="finding-content">
              <h4>{{ finding.title }}</h4>
              <p class="text-faint">{{ finding.target }}</p>
              <div class="finding-tags">
                <el-tag size="small" :type="finding.level === 'critical' ? 'danger' : 'warning'">
                  {{ finding.level === 'critical' ? 'Critical' : 'High' }}
                </el-tag>
                <el-tag size="small" effect="plain">{{ finding.category }}</el-tag>
              </div>
            </div>
            <span class="text-faint">{{ finding.time }}</span>
          </div>
        </div>
      </div>

      <div class="card-glass panel">
        <div class="panel-header">
          <div>
            <p class="text-faint">Activity pulse</p>
            <h3>Recent actions</h3>
          </div>
          <el-button text type="primary" size="small" @click="refreshUser">Refresh</el-button>
        </div>
        <div class="panel-body pulse">
          <el-timeline>
            <el-timeline-item
              v-for="(entry, index) in activityPulse"
              :key="index"
              :timestamp="entry.time"
              :type="entry.type"
              hollow
            >
              <strong>{{ entry.title }}</strong>
              <p class="text-faint">{{ entry.detail }}</p>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { DataLine, Monitor, Timer, WarningFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const userInfo = computed(() => auth.userInfo)

const kpiCards = [
  {
    title: 'Online assets',
    value: '142',
    caption: '+12%',
    subTitle: 'Live inventory updated continuously',
    icon: Monitor,
    tagType: 'success',
    tint: 'linear-gradient(135deg, rgba(16, 185, 129, 0.18), rgba(16, 185, 129, 0.05))',
  },
  {
    title: 'Critical ports',
    value: '87',
    caption: 'High priority',
    subTitle: 'Ports flagged across 17 critical hosts',
    icon: WarningFilled,
    tagType: 'danger',
    tint: 'linear-gradient(135deg, rgba(248, 113, 113, 0.16), rgba(239, 68, 68, 0.06))',
  },
  {
    title: 'Queued scans',
    value: '36',
    caption: 'Processing',
    subTitle: 'Estimated completion within 21 minutes',
    icon: Timer,
    tagType: 'warning',
    tint: 'linear-gradient(135deg, rgba(251, 191, 36, 0.16), rgba(234, 179, 8, 0.06))',
  },
  {
    title: 'Completed today',
    value: '18',
    caption: 'SLA steady',
    subTitle: 'Auto-dispatched to scan workers',
    icon: DataLine,
    tagType: 'info',
    tint: 'linear-gradient(135deg, rgba(59, 130, 246, 0.16), rgba(14, 165, 233, 0.06))',
  },
]

const ongoingTasks = [
  { name: 'Web application scan', owner: 'Blue Team · Core node', eta: '12m', progress: 62, stream: 'xray-web', status: 'running' },
  { name: 'Asset discovery · East', owner: 'Auto scheduler', eta: '24m', progress: 38, stream: 'fofa-sync', status: 'running' },
  { name: 'Port sweep', owner: 'Night batch', eta: 'Paused', progress: 45, stream: 'nmap-fast', status: 'paused' },
]

const assetsPreview = [
  { name: 'api.cloud.example', ip: '10.12.3.21', tags: ['Prod', 'API'], status: 'Online' },
  { name: 'cdn.edge.internal', ip: '172.19.4.11', tags: ['Static', 'High BW'], status: 'Online' },
  { name: 'jump.dev.lab', ip: '10.8.0.5', tags: ['Test', 'SSH'], status: 'Maintenance' },
]

const findings = [
  { title: 'Component exposure · Apache Struts2', target: 'api.cloud.example /443', category: 'Component', level: 'critical', time: '2m ago' },
  { title: 'Directory traversal attempts', target: 'cdn.edge.internal /static', category: 'Traffic', level: 'major', time: '27m ago' },
  { title: 'Weak credential attempts', target: 'jump.dev.lab /ssh', category: 'Auth', level: 'major', time: '1h ago' },
]

const activityPulse = [
  { title: 'Login verified', detail: 'User session refreshed and profile synced', time: 'Just now', type: 'success' },
  { title: 'Assets synchronized', detail: 'Inventory updated to 142 records', time: '10:24', type: 'primary' },
  { title: 'Baseline report generated', detail: 'Report published to notification channel', time: '09:10', type: 'warning' },
]

const refreshUser = async () => {
  await auth.fetchUserInfo()
}

const handleLogout = async () => {
  await auth.logout()
  router.replace({ name: 'Login' })
}

const goTasks = () => {
  router.push({ name: 'Tasks' })
}

onMounted(async () => {
  if (!auth.userInfo && auth.token) {
    await auth.fetchUserInfo()
  }
})
</script>

<style scoped>
.dashboard-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-radius: 16px;
}

.header-hint {
  margin-top: 6px;
}

.user-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  min-width: 160px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.kpi-card {
  display: grid;
  grid-template-columns: 56px 1fr;
  gap: 12px;
  padding: 14px;
  border-radius: 14px;
}

.kpi-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 14px;
  color: #e2e8f0;
}

.kpi-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kpi-value-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.kpi-value {
  font-size: 22px;
}

.kpi-sub {
  margin: 0;
  color: #94a3b8;
  font-size: 13px;
}

.panel-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.panel-grid.lower {
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
}

.panel {
  padding: 16px;
  border-radius: 16px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.panel-header h3 {
  margin: 4px 0 0;
}

.panel-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tasks .task-item {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.task-meta h4 {
  margin: 0 0 6px;
}

.task-progress {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.task-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.asset-table :deep(.el-table) {
  background: transparent;
  color: #e2e8f0;
}

.asset-table :deep(.el-table th),
.asset-table :deep(.el-table tr) {
  background-color: transparent;
}

.asset-table :deep(.el-table__body-wrapper) {
  background: transparent;
}

.tag-row {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.findings-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.finding-item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 10px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  align-items: center;
}

.finding-severity {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  color: #fee2e2;
}

.finding-severity.critical {
  background: linear-gradient(135deg, rgba(248, 113, 113, 0.2), rgba(239, 68, 68, 0.08));
}

.finding-severity.major {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.16), rgba(234, 179, 8, 0.08));
  color: #fef3c7;
}

.finding-content h4 {
  margin: 0 0 6px;
}

.finding-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.pulse :deep(.el-timeline-item__content) {
  color: #e2e8f0;
}

.pulse :deep(.el-timeline-item__timestamp) {
  color: #94a3b8;
}
</style>
