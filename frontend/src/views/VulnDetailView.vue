<template>
  <section class="detail-view">
    <header class="detail-header card-glass">
      <div>
        <p class="text-faint">结果详情</p>
        <h2 class="hero-title">漏洞详情</h2>
        <p class="text-faint">查看漏洞命中信息与证据摘要。</p>
      </div>
      <div class="header-actions">
        <el-button size="small" :loading="loading" @click="refreshDetail">刷新</el-button>
        <el-button size="small" @click="goBack">返回结果页</el-button>
      </div>
    </header>

    <section class="detail-body">
      <div class="card-glass detail-main">
        <div class="detail-title">
          <div>
            <h3>{{ vuln?.name || '未加载' }}</h3>
            <p class="text-faint">漏洞 ID #{{ vuln?.id ?? '-' }}</p>
          </div>
          <el-tag v-if="vuln" size="small" :type="severityTag(vuln.severity)" effect="dark">
            {{ vuln.severity.toUpperCase() }}
          </el-tag>
        </div>

        <div v-if="!vuln" class="empty-row">
          <el-empty description="暂无漏洞数据" />
        </div>

        <div v-else class="detail-grid">
          <div class="detail-item">
            <span class="text-faint">命中位置</span>
            <strong>{{ vuln.url || '未记录' }}</strong>
          </div>
          <div class="detail-item">
            <span class="text-faint">模板 ID</span>
            <strong>{{ vuln.template_id || '未记录' }}</strong>
          </div>
          <div class="detail-item">
            <span class="text-faint">关联 Host</span>
            <strong>{{ vuln.host_id ?? '-' }}</strong>
          </div>
          <div class="detail-item">
            <span class="text-faint">关联 Web</span>
            <strong>{{ vuln.http_service_id ?? '-' }}</strong>
          </div>
          <div class="detail-item">
            <span class="text-faint">发现时间</span>
            <strong>{{ formatTime(vuln.created_at) }}</strong>
          </div>
          <div class="detail-item">
            <span class="text-faint">更新时间</span>
            <strong>{{ formatTime(vuln.updated_at) }}</strong>
          </div>
        </div>

        <div v-if="vuln?.details" class="detail-section">
          <p class="text-faint">漏洞详情</p>
          <pre class="detail-json">{{ formatJson(vuln.details) }}</pre>
        </div>
      </div>

      <aside class="card-glass detail-aside">
        <h3>处理建议</h3>
        <p class="text-faint">结合命中 URL 与模板详情判断影响面，必要时补充复测。</p>
      </aside>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchVulnDetail, type VulnerabilitySummary } from '@/api/scan'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const vuln = ref<VulnerabilitySummary | null>(null)

const vulnId = computed(() => Number(route.params.vulnId || 0))
const assetId = computed(() => Number(route.query.assetId || 0))

const refreshDetail = async () => {
  if (!vulnId.value) {
    vuln.value = null
    return
  }
  loading.value = true
  try {
    vuln.value = await fetchVulnDetail(vulnId.value)
  } catch (error) {
    vuln.value = null
    ElMessage.error((error as Error).message)
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  if (assetId.value) {
    router.push({ name: 'Results', params: { assetId: assetId.value } })
    return
  }
  router.push({ name: 'Results' })
}

const severityTag = (severity: VulnerabilitySummary['severity']) => {
  switch (severity) {
    case 'critical':
    case 'high':
      return 'danger'
    case 'medium':
      return 'warning'
    default:
      return 'info'
  }
}

const formatTime = (value?: string | null) => {
  if (!value) return 'N/A'
  return new Date(value).toLocaleString()
}

const formatJson = (value: Record<string, unknown>) => JSON.stringify(value, null, 2)

onMounted(() => {
  refreshDetail()
})
</script>

<style scoped>
.detail-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  width: 100%;
}

.detail-header {
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

.detail-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 16px;
}

.detail-main {
  padding: 16px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-section {
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(2, 6, 23, 0.5);
  padding: 12px;
  display: grid;
  gap: 8px;
}

.detail-json {
  margin: 0;
  font-size: 12px;
  white-space: pre-wrap;
}

.detail-aside {
  padding: 16px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-row {
  padding: 12px;
}

.text-faint {
  color: #94a3b8;
}

@media (max-width: 1100px) {
  .detail-body {
    grid-template-columns: 1fr;
  }
}
</style>
