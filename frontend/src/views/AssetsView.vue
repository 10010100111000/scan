<template>
  <section class="assets-view">
    <header class="assets-header card-glass">
      <div>
        <p class="text-faint">Inventory</p>
        <h2 class="hero-title">Assets</h2>
        <p class="text-faint">Centralized asset list and exploration.</p>
      </div>
      <div class="assets-actions">
        <el-input v-model="query" size="small" clearable placeholder="Search asset" />
        <el-button type="primary" size="small">Export</el-button>
      </div>
    </header>

    <div class="card-glass assets-table">
      <el-table :data="filteredAssets" size="small" stripe>
        <el-table-column prop="name" label="Asset" min-width="180" />
        <el-table-column prop="type" label="Type" width="120" />
        <el-table-column prop="owner" label="Owner" width="160" />
        <el-table-column prop="updated" label="Updated" width="140" />
        <el-table-column prop="status" label="Status" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'Active' ? 'success' : 'info'">{{ row.status }}</el-tag>
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
  status: 'Active' | 'Paused'
}

const query = ref('')

const assets = ref<AssetItem[]>([
  { id: 1, name: 'api.cloud.example', type: 'Domain', owner: 'Blue Team', updated: 'Today', status: 'Active' },
  { id: 2, name: '10.12.3.21', type: 'IP', owner: 'Infra', updated: 'Yesterday', status: 'Active' },
  { id: 3, name: 'cdn.edge.internal', type: 'Domain', owner: 'Ops', updated: '2 days ago', status: 'Paused' },
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
