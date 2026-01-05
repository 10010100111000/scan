<template>
  <section class="dashboard-main">
    <header class="dashboard-header card-glass">
      <div>
        <p class="text-faint">欢迎回来</p>
        <h2 class="hero-title">Attack Surface 指挥中心</h2>
        <p class="text-faint header-hint">统一查看资产、调度扫描、跟踪暴露面。</p>
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
            <p class="text-faint">资产预览</p>
            <h3>最新资产</h3>
          </div>
          <el-button text type="primary" size="small">导出</el-button>
        </div>
        <div class="panel-body asset-table">
          <el-table :data="assetsPreview" size="small" border stripe>
            <el-table-column prop="name" label="资产" min-width="140" />
            <el-table-column prop="ip" label="IP / 域名" min-width="140" />
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
            <h3>近期暴露</h3>
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
                  {{ finding.level === 'critical' ? '高危' : '中高' }}
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
            <p class="text-faint">活动脉搏</p>
            <h3>近期动作</h3>
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
    title: '在线资产',
    value: '142',
    caption: '本周 +12%',
    subTitle: '资产数量持续更新',
    icon: Monitor,
    tagType: 'success',
    tint: 'linear-gradient(135deg, rgba(16, 185, 129, 0.18), rgba(16, 185, 129, 0.05))',
  },
  {
    title: '风险端口',
    value: '87',
    caption: '高优先级',
    subTitle: '覆盖 17 个关键主机',
    icon: WarningFilled,
    tagType: 'danger',
    tint: 'linear-gradient(135deg, rgba(248, 113, 113, 0.16), rgba(239, 68, 68, 0.06))',
  },
  {
    title: '待执行扫描',
    value: '36',
    caption: '排队中',
    subTitle: '预计 21 分钟内完成',
    icon: Timer,
    tagType: 'warning',
    tint: 'linear-gradient(135deg, rgba(251, 191, 36, 0.16), rgba(234, 179, 8, 0.06))',
  },
  {
    title: '今日完成',
    value: '18',
    caption: 'SLA 稳定',
    subTitle: '任务自动下发到扫描节点',
    icon: DataLine,
    tagType: 'info',
    tint: 'linear-gradient(135deg, rgba(59, 130, 246, 0.16), rgba(14, 165, 233, 0.06))',
  },
]


const assetsPreview = [
  { name: 'api.cloud.example', ip: '10.12.3.21', tags: ['生产', 'API'], status: '在线' },
  { name: 'cdn.edge.internal', ip: '172.19.4.11', tags: ['静态', '高带宽'], status: '在线' },
  { name: 'jump.dev.lab', ip: '10.8.0.5', tags: ['测试', 'SSH'], status: '维护' },
]

const findings = [
  { title: '组件风险 · Apache Struts2', target: 'api.cloud.example /443', category: '组件', level: 'critical', time: '2 分钟前' },
  { title: '目录遍历疑似请求', target: 'cdn.edge.internal /static', category: '流量', level: 'major', time: '27 分钟前' },
  { title: '弱口令尝试', target: 'jump.dev.lab /ssh', category: '鉴权', level: 'major', time: '1 小时前' },
]

const activityPulse = [
  { title: '登录验证成功', detail: '刷新会话并同步用户资料', time: '刚刚', type: 'success' },
  { title: '资产同步完成', detail: '资产池累计 142 条记录', time: '10:24', type: 'primary' },
  { title: '基线报告已生成', detail: '报告已推送到通知渠道', time: '09:10', type: 'warning' },
]

const refreshUser = async () => {
  await auth.fetchUserInfo()
}

const handleLogout = async () => {
  await auth.logout()
  router.replace({ name: 'Login' })
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
  width: 100%;
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
