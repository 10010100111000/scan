<template>
  <section class="detail-view">
    <header class="detail-header card-glass">
      <div>
        <p class="text-faint">结果详情</p>
        <h2 class="hero-title">主机详情</h2>
        <p class="text-faint">展示子域名/主机的解析信息与状态。</p>
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
            <h3>{{ host?.hostname || '未加载' }}</h3>
            <p class="text-faint">主机 ID #{{ host?.id ?? '-' }}</p>
          </div>
          <el-tag v-if="host" size="small" effect="dark">{{ host.status }}</el-tag>
        </div>

        <div v-if="!host" class="empty-row">
          <el-empty description="暂无主机数据" />
        </div>

        <div v-else class="detail-grid">
          <div class="detail-item">
            <span class="text-faint">解析 IP</span>
            <div v-if="host.ips && host.ips.length" class="ip-list">
              <div v-for="(ip, idx) in host.ips" :key="idx" class="ip-row">
                <strong>{{ ip.ip || ip }}</strong>
                <span v-if="ip.asn" class="asn-tag">{{ ip.asn }}</span>
              </div>
            </div>
            <strong v-else>暂无</strong>
          </div>
          <div class="detail-item">
            <span class="text-faint">项目 ID</span>
            <strong>{{ host.project_id }}</strong>
          </div>
          <div class="detail-item">
            <span class="text-faint">关联资产</span>
            <strong>{{ host.root_asset_id }}</strong>
          </div>
          <div class="detail-item">
            <span class="text-faint">创建时间</span>
            <strong>{{ formatTime(host.created_at) }}</strong>
          </div>
        </div>
      </div>

      <aside class="card-glass detail-aside">
        <h3>备注</h3>
        <p class="text-faint">主机详情用于核对解析 IP 与资产归属。</p>
      </aside>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchHostDetail, type HostSummary } from '@/api/scan'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const host = ref<HostSummary | null>(null)

const hostId = computed(() => Number(route.params.hostId || 0))
const assetId = computed(() => Number(route.query.assetId || 0))

const refreshDetail = async () => {
  if (!hostId.value) {
    host.value = null
    return
  }
  loading.value = true
  try {
    host.value = await fetchHostDetail(hostId.value)
  } catch (error) {
    host.value = null
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

const formatTime = (value?: string | null) => {
  if (!value) return 'N/A'
  return new Date(value).toLocaleString()
}

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

.ip-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ip-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.asn-tag {
  font-size: 12px;
  color: #94a3b8;
  background: rgba(148, 163, 184, 0.12);
  padding: 2px 6px;
  border-radius: 4px;
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
