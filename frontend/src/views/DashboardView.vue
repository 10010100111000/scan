<template>
  <div class="dashboard-page">
    <div class="background-accents"></div>
    <div class="dashboard-grid">
      <aside :class="['nav-rail', 'card-glass', { collapsed: railCollapsed }]">
        <div class="nav-rail__top">
          <div class="brand" v-if="!railCollapsed">
            <p class="brand__eyebrow">SCAN · 控制台</p>
            <h3>Attack Surface</h3>
          </div>
          <el-button circle size="small" @click="railCollapsed = !railCollapsed" aria-label="切换导航宽度">
            <el-icon>
              <component :is="railCollapsed ? Expand : Fold" />
            </el-icon>
          </el-button>
        </div>
        <el-button class="new-scan" type="primary" plain block @click="openScan">
          <el-icon><Plus /></el-icon>
          <span v-if="!railCollapsed">+ 新建扫描</span>
        </el-button>
        <div class="nav-list">
          <router-link
            v-for="item in navLinks"
            :key="item.label"
            :to="item.route"
            :class="['nav-item', { active: isActive(item.route) }]"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span v-if="!railCollapsed">{{ item.label }}</span>
          </router-link>
        </div>
      </aside>

      <main class="main-area">
        <header class="dashboard__header card-glass">
          <div>
            <p class="text-faint">欢迎回来</p>
            <h2 class="hero-title">临时控制台</h2>
            <p class="text-faint header-hint">示例数据演示资产与任务布局，真实数据接入后可直接替换。</p>
          </div>
          <div class="user-area">
            <div class="user-meta">
              <strong>{{ userInfo?.realName || userInfo?.username }}</strong>
              <span class="text-faint">{{ userInfo?.roles?.join(', ') || '访客' }}</span>
            </div>
            <el-avatar :size="40" :src="userInfo?.avatar">
              {{ userInfo?.username?.slice(0, 1).toUpperCase() }}
            </el-avatar>
            <el-button size="small" type="danger" @click="handleLogout">退出</el-button>
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
                <p class="text-faint">进行中的任务</p>
                <h3>Ongoing tasks</h3>
              </div>
              <el-button text type="primary" size="small">查看全部</el-button>
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
                    <el-tag v-if="task.status === 'paused'" size="small" type="warning" effect="plain">暂停</el-tag>
                    <el-tag v-else size="small" type="success" effect="plain">运行中</el-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="card-glass panel">
            <div class="panel-header">
              <div>
                <p class="text-faint">资产摘录</p>
                <h3>Asset preview</h3>
              </div>
              <el-button text type="primary" size="small">导出</el-button>
            </div>
            <div class="panel-body asset-table">
              <el-table :data="assetsPreview" size="small" border stripe>
                <el-table-column prop="name" label="资产" min-width="140" />
                <el-table-column prop="ip" label="IP/域名" min-width="140" />
                <el-table-column label="标签" min-width="160">
                  <template #default="{ row }">
                    <div class="tag-row">
                      <el-tag v-for="tag in row.tags" :key="tag" size="small" effect="plain">{{ tag }}</el-tag>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="row.status === '在线' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
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
                <p class="text-faint">最新发现</p>
                <h3>Recent findings</h3>
              </div>
              <el-button text type="primary" size="small">导出报告</el-button>
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
                      {{ finding.level === 'critical' ? '高危' : '中危' }}
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
                <p class="text-faint">片刻速览</p>
                <h3>Activity pulse</h3>
              </div>
              <el-button text type="primary" size="small" @click="refreshUser">刷新</el-button>
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
      </main>

      <aside class="right-rail">
        <div class="card-glass rail-card">
          <div class="panel-header">
            <div>
              <p class="text-faint">快捷筛选</p>
              <h3>Quick filters</h3>
            </div>
            <el-button text size="small" type="primary">更多</el-button>
          </div>
          <div class="filter-tags">
            <el-tag v-for="filter in quickFilters" :key="filter" size="large" effect="plain" class="filter-tag">
              {{ filter }}
            </el-tag>
          </div>
          <el-button type="primary" plain block size="small">保存过滤器</el-button>
        </div>

        <div class="card-glass rail-card">
          <div class="panel-header">
            <div>
              <p class="text-faint">队列中的任务</p>
              <h3>Queued jobs</h3>
            </div>
          </div>
          <div class="queue-list">
            <div v-for="job in queuedJobs" :key="job.name" class="queue-item">
              <div>
                <h4>{{ job.name }}</h4>
                <p class="text-faint">{{ job.scope }}</p>
              </div>
              <el-tag :type="job.state === '等待' ? 'warning' : 'info'" size="small">{{ job.state }}</el-tag>
            </div>
          </div>
        </div>

        <div class="card-glass rail-card">
          <div class="panel-header">
            <div>
              <p class="text-faint">帮助 & 链接</p>
              <h3>Helpful links</h3>
            </div>
          </div>
          <ul class="links">
            <li v-for="link in helpfulLinks" :key="link.label">
              <el-icon><Link /></el-icon>
              <div>
                <p>{{ link.label }}</p>
                <span class="text-faint">{{ link.desc }}</span>
              </div>
            </li>
          </ul>
        </div>
      </aside>
    </div>
    <transition name="scan-overlay">
      <div v-if="scanOverlayOpen" class="scan-overlay" @click.self="closeScan">
        <div class="scan-overlay__backdrop" @click="closeScan"></div>
        <div class="scan-overlay__panel" @click.stop>
          <button class="scan-overlay__close" type="button" @click="closeScan" aria-label="Close scan overlay">
            <span aria-hidden="true">&times;</span>
          </button>
          <ScanView />
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch, type Component } from 'vue'
import { useRoute, useRouter, type RouteLocationRaw } from 'vue-router'
import {
  Compass,
  DataBoard,
  DataLine,
  Expand,
  Fold,
  Link,
  Monitor,
  Plus,
  Timer,
  User,
  WarningFilled,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import ScanView from '@/views/ScanView.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const userInfo = computed(() => auth.userInfo)
const railCollapsed = ref(false)
const scanOverlayOpen = ref(false)

const openScan = () => {
  scanOverlayOpen.value = true
}

const closeScan = () => {
  scanOverlayOpen.value = false
}

const handleKeydown = (event: KeyboardEvent) => {
  if (!scanOverlayOpen.value) {
    return
  }
  if (event.key === 'Escape') {
    closeScan()
  }
}


const navLinks: Array<{ label: string; icon: Component; route: RouteLocationRaw }> = [
  { label: '仪表盘', icon: DataBoard, route: { name: 'Dashboard' } },
  { label: '任务流', icon: Timer, route: { name: 'Dashboard', query: { section: 'tasks' } } },
  { label: '资产清单', icon: Monitor, route: { name: 'Dashboard', query: { section: 'assets' } } },
  { label: '初始化', icon: Compass, route: { name: 'Setup' } },
  { label: '登录/切换', icon: User, route: { name: 'Login' } },
]

const kpiCards = [
  {
    title: '在线资产',
    value: '142',
    caption: '本周 +12%',
    subTitle: '活跃数量实时刷新',
    icon: Monitor,
    tagType: 'success',
    tint: 'linear-gradient(135deg, rgba(16, 185, 129, 0.18), rgba(16, 185, 129, 0.05))',
  },
  {
    title: '风险端口',
    value: '87',
    caption: '高危优先',
    subTitle: '扫描端口中 17 个高危',
    icon: WarningFilled,
    tagType: 'danger',
    tint: 'linear-gradient(135deg, rgba(248, 113, 113, 0.16), rgba(239, 68, 68, 0.06))',
  },
  {
    title: '待扫描',
    value: '36',
    caption: '队列中',
    subTitle: '预计 21 分钟内完成',
    icon: Timer,
    tagType: 'warning',
    tint: 'linear-gradient(135deg, rgba(251, 191, 36, 0.16), rgba(234, 179, 8, 0.06))',
  },
  {
    title: '今日完成',
    value: '18',
    caption: 'SLA 正常',
    subTitle: '自动分发到扫描节点',
    icon: DataLine,
    tagType: 'info',
    tint: 'linear-gradient(135deg, rgba(59, 130, 246, 0.16), rgba(14, 165, 233, 0.06))',
  },
]

const ongoingTasks = [
  { name: 'Web 应用扫描', owner: '蓝队 · 默认节点', eta: '12m', progress: 62, stream: 'xray-web', status: 'running' },
  { name: '资产发现 · 东区', owner: '自动调度', eta: '24m', progress: 38, stream: 'fofa-sync', status: 'running' },
  { name: '端口巡检', owner: '夜间批次', eta: '暂停', progress: 45, stream: 'nmap-fast', status: 'paused' },
]

const assetsPreview = [
  { name: 'api.cloud.example', ip: '10.12.3.21', tags: ['生产', 'API'], status: '在线' },
  { name: 'cdn.edge.internal', ip: '172.19.4.11', tags: ['静态', '高带宽'], status: '在线' },
  { name: 'jump.dev.lab', ip: '10.8.0.5', tags: ['测试', 'SSH'], status: '维护' },
]

const findings = [
  { title: '组件漏洞 · Apache Struts2', target: 'api.cloud.example /443', category: '组件', level: 'critical', time: '2 分钟前' },
  { title: '目录遍历可疑请求', target: 'cdn.edge.internal /static', category: '流量', level: 'major', time: '27 分钟前' },
  { title: '弱口令尝试', target: 'jump.dev.lab /ssh', category: '鉴权', level: 'major', time: '1 小时前' },
]

const activityPulse = [
  { title: '登录校验成功', detail: '重新拉取用户信息并更新缓存', time: '刚刚', type: 'success' },
  { title: '资产同步完成', detail: '资产池累计 142 条记录', time: '10:24', type: 'primary' },
  { title: '生成基线报告', detail: '今日报告已推送至通知渠道', time: '09:10', type: 'warning' },
]

const queuedJobs = [
  { name: '夜间全量扫描', scope: '120 个目标 · 5 节点', state: '等待' },
  { name: '目录爆破', scope: 'api.cloud.example', state: '准备中' },
  { name: '合规检查', scope: '生产资产', state: '等待' },
]

const quickFilters = ['仅高危', '新增资产', '需要确认', '今日', '外部暴露']

const helpfulLinks = [
  { label: '如何接入真实数据', desc: '查看接口文档与示例' },
  { label: '风险处置指南', desc: '默认优先级与打分规则' },
  { label: '反馈/需求收集', desc: '提交至产品待办池' },
]

const refreshUser = async () => {
  await auth.fetchUserInfo()
}

const handleLogout = async () => {
  await auth.logout()
  router.replace({ name: 'Login' })
}

const isActive = (navRoute: RouteLocationRaw) => router.resolve(navRoute).href === route.fullPath

onMounted(async () => {
  if (!auth.userInfo && auth.token) {
    await auth.fetchUserInfo()
  }
})

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.body.classList.remove('scan-overlay-open')
})

watch(scanOverlayOpen, (isOpen) => {
  document.body.classList.toggle('scan-overlay-open', isOpen)
})
</script>

<style scoped>
.dashboard-page {
  position: relative;
  min-height: 100vh;
  padding: 24px;
  color: #e2e8f0;
  background: radial-gradient(circle at 12% 20%, rgba(56, 189, 248, 0.12), transparent 25%),
    radial-gradient(circle at 85% 10%, rgba(139, 92, 246, 0.12), transparent 26%),
    radial-gradient(circle at 30% 70%, rgba(94, 234, 212, 0.08), transparent 30%),
    linear-gradient(135deg, #0b1224 0%, #0d1830 35%, #0a0f1f 100%);
}

.background-accents {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(circle at 70% 30%, rgba(59, 130, 246, 0.08), transparent 30%);
  filter: blur(24px);
  opacity: 0.8;
}

.dashboard-grid {
  position: relative;
  display: grid;
  grid-template-columns: 260px 1fr 320px;
  gap: 16px;
  z-index: 1;
}

.nav-rail {
  position: sticky;
  top: 16px;
  align-self: start;
  height: calc(100vh - 32px);
  padding: 16px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: width 0.2s ease, padding 0.2s ease;
  width: 260px;
}

.nav-rail.collapsed {
  width: 84px;
  padding: 16px 12px;
}

.nav-rail__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.brand__eyebrow {
  margin: 0;
  letter-spacing: 0.08em;
  font-size: 12px;
  text-transform: uppercase;
  color: #94a3b8;
}

.brand h3 {
  margin: 4px 0 0;
}

.new-scan {
  justify-content: center;
}

.new-scan .el-icon {
  margin-right: 6px;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  color: #cbd5e1;
  transition: background 0.2s ease, color 0.2s ease;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #e2e8f0;
}

.nav-item.active {
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.18), rgba(99, 102, 241, 0.08));
  color: #f8fafc;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.nav-rail.collapsed .nav-item {
  justify-content: center;
}

.main-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dashboard__header {
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

.right-rail {
  position: sticky;
  top: 16px;
  align-self: start;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.rail-card {
  padding: 16px;
  border-radius: 16px;
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.filter-tag {
  padding: 8px 12px;
}

.queue-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.queue-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.links {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.links li {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  padding: 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  align-items: center;
}

.links p {
  margin: 0;
}

.card-glass {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(12px);
}

.text-faint {
  color: #9ca3af;
}

.hero-title {
  font-size: 26px;
  font-weight: 700;
  color: #e2e8f0;
}

:global(body.scan-overlay-open) {
  overflow: hidden;
}

.scan-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: grid;
}

.scan-overlay__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(2, 6, 23, 0.72);
  backdrop-filter: blur(2px);
}

.scan-overlay__panel {
  position: relative;
  margin-top: auto;
  height: 100%;
  width: 100%;
  background: #0b1020;
  box-shadow: 0 -24px 80px rgba(0, 0, 0, 0.4);
  overflow: auto;
}

.scan-overlay__close {
  position: fixed;
  top: 18px;
  right: 18px;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: rgba(15, 23, 42, 0.8);
  color: #e2e8f0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 2101;
  transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.scan-overlay__close:hover {
  transform: translateY(-1px);
  border-color: rgba(226, 232, 240, 0.5);
  background: rgba(30, 41, 59, 0.9);
}

.scan-overlay-enter-active,
.scan-overlay-leave-active {
  transition: opacity 0.2s ease;
}

.scan-overlay-enter-from,
.scan-overlay-leave-to {
  opacity: 0;
}

.scan-overlay-enter-active .scan-overlay__panel,
.scan-overlay-leave-active .scan-overlay__panel {
  transition: transform 0.35s ease;
}

.scan-overlay-enter-from .scan-overlay__panel,
.scan-overlay-leave-to .scan-overlay__panel {
  transform: translateY(100%);
}

@media (max-width: 1280px) {
  .dashboard-grid {
    grid-template-columns: 220px 1fr;
  }

  .right-rail {
    display: none;
  }
}

@media (max-width: 960px) {
  .dashboard-page {
    padding: 16px;
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .nav-rail {
    height: auto;
    position: relative;
    width: 100%;
    flex-direction: row;
    align-items: center;
    flex-wrap: wrap;
  }

  .nav-rail.collapsed {
    width: 100%;
  }

  .nav-list {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .nav-item {
    flex: 1 1 120px;
  }

  .nav-rail.collapsed .nav-item {
    flex: 0 0 60px;
  }

  .tasks .task-item {
    grid-template-columns: 1fr;
  }
}
</style>
