<template>
  <section class="assets-view">
    <header class="assets-header card-glass">
      <div>
        <p class="text-faint">资产库</p>
        <h2 class="hero-title">资产</h2>
        <p class="text-faint">集中管理与查看资产详情。</p>
      </div>
      <div class="assets-actions">
        <el-input v-model="query" size="small" clearable placeholder="搜索资产" />
        <el-button type="primary" size="small">导出</el-button>
      </div>
    </header>

    <div class="card-glass assets-table">
      <el-table :data="filteredAssets" size="small" stripe>
        <el-table-column prop="name" label="资产" min-width="180" />
        <el-table-column prop="type" label="类型" width="120" />
        <el-table-column prop="owner" label="负责人" width="160" />
        <el-table-column prop="updated" label="更新时间" width="140" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === '活跃' ? 'success' : 'info'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

type AssetItem = {
  id: number
  name: string
  type: string
  owner: string
  updated: string
  status: '活跃' | '暂停'
}

const query = ref('')

const assets = ref<AssetItem[]>([
  { id: 1, name: 'api.cloud.example', type: 'Domain', owner: '蓝队', updated: '今天', status: '活跃' },
  { id: 2, name: '10.12.3.21', type: 'IP', owner: '基础设施', updated: '昨天', status: '活跃' },
  { id: 3, name: 'cdn.edge.internal', type: 'Domain', owner: '运维', updated: '2 天前', status: '暂停' },
])

const filteredAssets = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  if (!keyword) {
    return assets.value
  }
  return assets.value.filter((asset) => asset.name.toLowerCase().includes(keyword))
})
</script>

<style scoped>
.assets-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  width: 100%;
}

.assets-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 16px;
}

.assets-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.assets-table {
  padding: 16px;
  border-radius: 16px;
}

.assets-table :deep(.el-table) {
  background: transparent;
  color: #e2e8f0;
}

.assets-table :deep(.el-table th),
.assets-table :deep(.el-table tr) {
  background-color: transparent;
}

.assets-table :deep(.el-table__body-wrapper) {
  background: transparent;
}
</style>
