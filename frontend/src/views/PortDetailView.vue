<template>
  <section class="detail-view">
    <header class="detail-header card-glass">
      <div>
        <p class="text-faint">结果详情</p>
        <h2 class="hero-title">端口详情</h2>
        <p class="text-faint">查看端口与服务信息。</p>
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
            <h3>{{ portLabel }}</h3>
            <p class="text-faint">端口 ID #{{ port?.id ?? '-' }}</p>
          </div>
          <el-tag v-if="port" size="small" effect="dark">{{ port.service || '未知服务' }}</el-tag>
        </div>

        <div v-if="!port" class="empty-row">
          <el-empty description="暂无端口数据" />
        </div>

        <div v-else class="detail-grid">
          <div class="detail-item">
            <span class="text-faint">IP</span>
            <strong>{{ port.ip || '-' }}</strong>
          </div>
          <div class="detail-item">
            <span class="text-faint">端口</span>
            <strong>{{ port.port }}</strong>
          </div>
          <div class="detail-item">
            <span class="text-faint">服务</span>
            <strong>{{ port.service || '未知' }}</strong>
          </div>
          <div class="detail-item">
            <span class="text-faint">关联资产</span>
            <strong>{{ port.root_asset_id ?? '-' }}</strong>
          </div>
        </div>
      </div>

      <aside class="card-glass detail-aside">
        <h3>备注</h3>
        <p class="text-faint">端口详情用于确认资产开放端口与服务。</p>
      </aside>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchPortDetail, type PortSummary } from '@/api/scan'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const port = ref<PortSummary | null>(null)

const portId = computed(() => Number(route.params.portId || 0))
const assetId = computed(() => Number(route.query.assetId || 0))

const portLabel = computed(() => {
  if (!port.value) return '未加载'
  return `${port.value.ip || '-'}:${port.value.port}`
})

const refreshDetail = async () => {
  if (!portId.value) {
    port.value = null
    return
  }
  loading.value = true
  try {
    port.value = await fetchPortDetail(portId.value)
  } catch (error) {
    port.value = null
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
