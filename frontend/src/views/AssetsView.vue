<template>
  <section class="assets-view">
    <header class="assets-header card-glass">
      <div>
        <p class="text-faint">Global Inventory</p>
        <h2 class="hero-title">资产库</h2>
        <p class="text-faint">查看所有项目的资产概览。</p>
      </div>
      <div class="assets-actions">
        <el-input 
          v-model="searchQuery" 
          size="default" 
          clearable 
          placeholder="搜索资产名称..." 
          @keyup.enter="handleSearch"
          @clear="handleSearch"
          class="w-64"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button :icon="Refresh" circle @click="loadData" />
      </div>
    </header>

    <div class="card-glass assets-table-container" v-loading="loading">
      <el-table :data="assets" size="default" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column label="资产名称" min-width="200">
          <template #default="{ row }">
            <span class="font-medium text-blue-600 dark:text-blue-400">{{ row.name }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
             <el-tag :type="row.type === 'domain' ? '' : 'warning'" size="small" effect="plain">
               {{ row.type.toUpperCase() }}
             </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="所属项目ID" width="120" align="center">
          <template #default="{ row }">
            <span class="text-gray-500">#{{ row.project_id }}</span>
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            <span class="text-gray-500 text-sm">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="goToDetail(row.id)">详情</el-button>
            <el-button link type="primary" size="small" @click="runQuickScan(row)">扫描</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-bar">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          :total="total" 
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
          background
        />
        </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
// 引入新定义的 API
import { fetchGlobalAssets, triggerScan, type Asset } from '@/api/scan'

const router = useRouter()

// --- 状态定义 ---
const loading = ref(false)
const assets = ref<Asset[]>([])
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0) // 后端目前没返回 total，后续需要后端支持

// --- 核心逻辑 ---

const loadData = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    
    // 调用全局资产接口
    const res = await fetchGlobalAssets({
      skip,
      limit: pageSize.value,
      search: searchQuery.value || undefined
    })

    // 兼容处理：检查返回的是数组还是包含 items 的对象
    // 根据目前的 backend 代码，它是直接返回数组 data
    const list = Array.isArray(res) ? res : (res['data'] || [])
    
    assets.value = list
    // total.value = res.total || 0  // 暂时注释，等后端加上 total 字段
    
  } catch (error) {
    console.error(error)
    ElMessage.error('加载资产列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1 // 重置到第一页
  loadData()
}

// 分页
const handleSizeChange = (val: number) => {
  pageSize.value = val
  loadData()
}
const handlePageChange = (val: number) => {
  currentPage.value = val
  loadData()
}

// 格式化时间
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

// 跳转详情
const goToDetail = (id: number) => {
  router.push(`/results/${id}`) // 假设这是详情页路由
}

// 快速扫描 (调用新的 Scans API)
const runQuickScan = async (row: Asset) => {
  try {
    ElMessage.info(`正在为 ${row.name} 启动快速扫描...`)
    await triggerScan({
      asset_id: row.id,
      strategy_name: '1. 域名快速侦察 (Web)' // 暂时硬编码一个默认策略，或者弹窗让用户选
    })
    ElMessage.success('扫描任务已提交')
    router.push('/tasks')
  } catch (e) {
    ElMessage.error('启动扫描失败')
  }
}

// 初始化
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.assets-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  width: 100%;
  padding-bottom: 2rem;
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

.assets-table-container {
  padding: 16px;
  border-radius: 16px;
  min-height: 400px;
}

/* 透视卡片风格适配 */
.assets-table-container :deep(.el-table) {
  background: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: transparent;
}

.assets-table-container :deep(.el-table th) {
  background-color: transparent !important;
  color: #64748b; /* text-slate-500 */
}

.assets-table-container :deep(.el-table td) {
  background-color: transparent !important;
}

.pagination-bar {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>