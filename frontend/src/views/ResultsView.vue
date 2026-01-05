<template>
  <section class="results-view">
    <header class="results-header card-glass">
      <div>
        <p class="text-faint">结果中心</p>
        <h2 class="hero-title">扫描结果详情</h2>
        <p class="text-faint">结果按资产归档，域名关注子域名与 Web，IP/CIDR 关注端口与服务。</p>
      </div>
      <div class="results-actions">
        <el-input v-model="query" size="small" clearable placeholder="搜索结果" />
        <el-button size="small" type="primary" :loading="loading" @click="refreshAll">刷新</el-button>
        <el-button size="small" @click="goTasks">返回任务中心</el-button>
      </div>
    </header>

    <section class="results-body">
      <div class="card-glass results-main">
        <div class="results-hero">
          <div>
            <h3>{{ assetTitle }}</h3>
            <p class="text-faint">{{ assetSubtitle }}</p>
          </div>
          <el-tag size="small" effect="dark">{{ assetTypeLabel }}</el-tag>
        </div>

        <el-alert
          v-if="assetMissing"
          type="warning"
          title="未找到资产"
          description="请从任务中心进入结果详情，或确认资产 ID 是否正确。"
          show-icon
        />

        <el-tabs v-if="!assetMissing" v-model="activeTab" class="results-tabs">
          <el-tab-pane v-if="isDomain" label="子域名" name="hosts">
            <div class="result-list">
              <div v-if="filteredHosts.length === 0" class="empty-row">
                <el-empty description="暂无子域名结果" />
              </div>
              <div v-for="host in filteredHosts" :key="host.id" class="result-row">
                <div>
                  <strong>{{ host.hostname }}</strong>
                  <p class="text-faint">{{ host.ips.join(', ') || '暂无解析 IP' }}</p>
                </div>
                <el-tag size="small" effect="plain">{{ host.status }}</el-tag>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane v-if="!isDomain" label="端口" name="ports">
            <div class="result-list">
              <div v-if="filteredPorts.length === 0" class="empty-row">
                <el-empty description="暂无端口结果" />
              </div>
              <div v-for="port in filteredPorts" :key="port.id" class="result-row">
                <div>
                  <strong>{{ port.ip }}:{{ port.port }}</strong>
                  <p class="text-faint">{{ port.service || '未知服务' }}</p>
                </div>
                <el-tag size="small" effect="plain">端口</el-tag>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="Web 服务" name="web">
            <div class="result-list">
              <div v-if="filteredWeb.length === 0" class="empty-row">
                <el-empty description="暂无 Web 结果" />
              </div>
              <div v-for="service in filteredWeb" :key="service.id" class="result-row">
                <div>
                  <strong>{{ service.url }}</strong>
                  <p class="text-faint">{{ service.title || '未识别标题' }}</p>
                </div>
                <el-tag size="small" effect="plain">{{ service.status || '未知' }}</el-tag>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="漏洞" name="vulns">
            <div class="result-list">
              <div v-if="filteredVulns.length === 0" class="empty-row">
                <el-empty description="暂无漏洞结果" />
              </div>
              <div v-for="vuln in filteredVulns" :key="vuln.id" class="result-row">
                <div>
                  <strong>{{ vuln.name }}</strong>
                  <p class="text-faint">{{ vuln.url || '未记录 URL' }}</p>
                </div>
                <el-tag size="small" :type="severityTag(vuln.severity)" effect="dark">
                  {{ vuln.severity.toUpperCase() }}
                </el-tag>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <aside class="card-glass results-aside">
        <h3>归档信息</h3>
        <div class="aside-list">
          <div class="aside-row">
            <span class="text-faint">资产 ID</span>
            <strong>{{ asset?.id ?? '-' }}</strong>
          </div>
          <div class="aside-row">
            <span class="text-faint">资产名称</span>
            <strong>{{ asset?.name ?? '-' }}</strong>
          </div>
          <div class="aside-row">
            <span class="text-faint">项目</span>
            <strong>{{ assetProjectLabel }}</strong>
          </div>
          <div class="aside-row">
            <span class="text-faint">创建时间</span>
            <strong>{{ assetCreatedAt }}</strong>
          </div>
        </div>

        <div class="aside-section">
          <p class="text-faint">结果概览</p>
          <div class="stats-grid">
            <div class="stat-card">
              <p class="text-faint">子域名</p>
              <strong>{{ hosts.length }}</strong>
            </div>
            <div class="stat-card">
              <p class="text-faint">端口</p>
              <strong>{{ ports.length }}</strong>
            </div>
            <div class="stat-card">
              <p class="text-faint">Web</p>
              <strong>{{ webServices.length }}</strong>
            </div>
            <div class="stat-card">
              <p class="text-faint">漏洞</p>
              <strong>{{ vulns.length }}</strong>
            </div>
          </div>
        </div>
      </aside>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  fetchAssetById,
  fetchAssetHosts,
  fetchAssetPorts,
  fetchAssetVulns,
  fetchAssetWeb,
  type Asset,
  type HostSummary,
  type HTTPServiceSummary,
  type PortSummary,
  type VulnerabilitySummary,
} from '@/api/scan'

const route = useRoute()
const router = useRouter()
const query = ref('')
const loading = ref(false)
const activeTab = ref('hosts')

const asset = ref<Asset | null>(null)
const hosts = ref<HostSummary[]>([])
const ports = ref<PortSummary[]>([])
const webServices = ref<HTTPServiceSummary[]>([])
const vulns = ref<VulnerabilitySummary[]>([])

const assetId = computed(() => Number(route.params.assetId || 0))
const assetMissing = computed(() => !asset.value)
// 域名资产优先展示子域名，IP/CIDR 资产优先展示端口与服务
const isDomain = computed(() => asset.value?.type === 'domain')

const assetTitle = computed(() => asset.value?.name || '未选择资产')
const assetSubtitle = computed(() => (asset.value ? `结果归档到项目 #${asset.value.project_id}` : '请从任务中心进入'))
const assetTypeLabel = computed(() => {
  if (!asset.value) {
    return '未指定'
  }
  return isDomain.value ? '域名资产' : 'IP/CIDR 资产'
})
const assetProjectLabel = computed(() => (asset.value ? `项目 #${asset.value.project_id}` : '-'))
const assetCreatedAt = computed(() => (asset.value ? new Date(asset.value.created_at).toLocaleString() : '-'))

const filteredHosts = computed(() => {
  if (!query.value.trim()) {
    return hosts.value
  }
  const keyword = query.value.trim().toLowerCase()
  return hosts.value.filter((host) => host.hostname.toLowerCase().includes(keyword))
})

const filteredPorts = computed(() => {
  if (!query.value.trim()) {
    return ports.value
  }
  const keyword = query.value.trim().toLowerCase()
  return ports.value.filter((port) => `${port.ip}:${port.port}`.includes(keyword))
})

const filteredWeb = computed(() => {
  if (!query.value.trim()) {
    return webServices.value
  }
  const keyword = query.value.trim().toLowerCase()
  return webServices.value.filter((service) => {
    return service.url.toLowerCase().includes(keyword) || (service.title || '').toLowerCase().includes(keyword)
  })
})

const filteredVulns = computed(() => {
  if (!query.value.trim()) {
    return vulns.value
  }
  const keyword = query.value.trim().toLowerCase()
  return vulns.value.filter((vuln) => {
    return vuln.name.toLowerCase().includes(keyword) || (vuln.url || '').toLowerCase().includes(keyword)
  })
})

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

const loadAsset = async () => {
  if (!assetId.value) {
    asset.value = null
    return
  }
  asset.value = await fetchAssetById(assetId.value)
}

const loadResults = async () => {
  if (!asset.value) {
    return
  }
  const id = asset.value.id
  const [hostData, portData, webData, vulnData] = await Promise.all([
    fetchAssetHosts(id, { limit: 50 }),
    fetchAssetPorts(id, { limit: 50 }),
    fetchAssetWeb(id, { limit: 50 }),
    fetchAssetVulns(id, { limit: 50 }),
  ])
  hosts.value = hostData.items
  ports.value = portData
  webServices.value = webData
  vulns.value = vulnData
}

const refreshAll = async () => {
  loading.value = true
  try {
    await loadAsset()
    if (!asset.value) {
      return
    }
    await loadResults()
    activeTab.value = isDomain.value ? 'hosts' : 'ports'
  } catch (error) {
    asset.value = null
    ElMessage.error((error as Error).message)
  } finally {
    loading.value = false
  }
}

const goTasks = () => {
  router.push({ name: 'Tasks' })
}

watch(assetId, () => {
  refreshAll()
})

onMounted(() => {
  refreshAll()
})
</script>

<style scoped>
.results-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  width: 100%;
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 16px;
}

.results-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.results-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
}

.results-main {
  padding: 16px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.results-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.results-tabs :deep(.el-tabs__nav-wrap::after) {
  background: rgba(148, 163, 184, 0.12);
}

.result-list {
  display: grid;
  gap: 12px;
}

.result-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.empty-row {
  padding: 12px;
}

.results-aside {
  padding: 16px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.aside-list {
  display: grid;
  gap: 10px;
}

.aside-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.aside-section {
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(2, 6, 23, 0.5);
  padding: 12px;
  display: grid;
  gap: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.stat-card {
  border-radius: 12px;
  padding: 10px;
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid rgba(148, 163, 184, 0.12);
  display: grid;
  gap: 6px;
}

.text-faint {
  color: #94a3b8;
}

@media (max-width: 1100px) {
  .results-body {
    grid-template-columns: 1fr;
  }
}
</style>
