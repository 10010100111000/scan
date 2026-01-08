<template>
  <div class="h-full w-full fade-in flex flex-col gap-4 p-4 md:p-6">
    
    <header class="card-glass p-6 rounded-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shrink-0">
      <div class="flex gap-5 items-center">
        <div class="w-16 h-16 rounded-xl flex items-center justify-center text-3xl shadow-lg border border-white/5 shrink-0"
             :class="assetInfo?.type === 'domain' ? 'bg-blue-600/20 text-blue-400' : 'bg-purple-600/20 text-purple-400'">
          <el-icon><component :is="assetInfo?.type === 'domain' ? 'Globe' : 'Connection'" /></el-icon>
        </div>
        
        <div>
          <div class="flex items-center gap-3">
            <h1 class="text-2xl md:text-3xl font-black text-slate-100 tracking-tight truncate max-w-[300px] md:max-w-md" :title="assetInfo?.name">
              {{ assetInfo?.name || 'Loading...' }}
            </h1>
            <el-tag v-if="assetInfo?.type" size="small" effect="dark" class="uppercase font-bold tracking-wider border-none" 
                    :color="assetInfo.type === 'domain' ? '#2563eb' : '#9333ea'">
              {{ assetInfo.type }}
            </el-tag>
          </div>
          <p class="text-slate-500 text-sm mt-1 font-mono flex items-center gap-2">
            <span>ID: {{ assetId }}</span>
            <span class="w-1 h-1 rounded-full bg-slate-600"></span>
            <span>Added: {{ formatDate(assetInfo?.created_at) }}</span>
          </p>
        </div>
      </div>

      <div class="flex items-center gap-4 self-end md:self-auto">
        <div class="hidden lg:flex gap-3 mr-4">
          <div class="text-center px-4 py-1.5 bg-slate-800/50 rounded-lg border border-slate-700/50">
             <div class="text-xl font-bold text-red-400">{{ vulns.length }}</div>
             <div class="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Vulns</div>
          </div>
          <div class="text-center px-4 py-1.5 bg-slate-800/50 rounded-lg border border-slate-700/50">
             <div class="text-xl font-bold text-blue-400">{{ ports.length }}</div>
             <div class="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Ports</div>
          </div>
        </div>

        <div class="flex gap-2">
           <el-button type="primary" :icon="Lightning" @click="handleRescan" :loading="scanning">
             立即扫描
           </el-button>
           <el-dropdown trigger="click" @command="handleCommand">
             <el-button plain type="info" :icon="MoreFilled" class="!px-3" />
             <template #dropdown>
               <el-dropdown-menu class="glass-dropdown">
                 <el-dropdown-item command="delete" class="text-red-400">
                   <el-icon><Delete /></el-icon> 删除资产
                 </el-dropdown-item>
               </el-dropdown-menu>
             </template>
           </el-dropdown>
        </div>
      </div>
    </header>

    <div class="card-glass flex-1 rounded-2xl overflow-hidden flex flex-col min-h-0 relative">
      <el-tabs v-model="activeTab" class="glass-tabs h-full flex flex-col">
        
        <el-tab-pane label="漏洞风险" name="vulns" class="h-full flex flex-col">
           <div class="flex-1 overflow-y-auto custom-scrollbar p-0">
             <el-table :data="vulns" style="width: 100%" class="glass-table" empty-text="暂无漏洞数据">
               <el-table-column label="Severity" width="100" sortable prop="severity">
                 <template #default="{ row }">
                   <el-tag size="small" effect="dark" :type="getSeverityType(row.severity)" class="border-none font-bold">
                     {{ row.severity.toUpperCase() }}
                   </el-tag>
                 </template>
               </el-table-column>
               
               <el-table-column prop="title" label="Vulnerability Name" min-width="250">
                  <template #default="{ row }">
                    <span class="font-bold text-slate-200">{{ row.title }}</span>
                  </template>
               </el-table-column>
               
               <el-table-column prop="vulnerability_id" label="Template / CVE" width="200">
                  <template #default="{ row }">
                    <span v-if="row.vulnerability_id" class="font-mono text-xs text-blue-300 bg-blue-900/30 px-2 py-0.5 rounded border border-blue-500/30">
                      {{ row.vulnerability_id }}
                    </span>
                    <span v-else class="text-slate-600">-</span>
                  </template>
               </el-table-column>
               
               <el-table-column prop="matched_at" label="Matched URL" min-width="300" show-overflow-tooltip>
                 <template #default="{ row }">
                   <a :href="row.matched_at" target="_blank" class="text-slate-400 hover:text-blue-400 hover:underline transition-colors">
                     {{ row.matched_at }}
                   </a>
                 </template>
               </el-table-column>
             </el-table>
           </div>
        </el-tab-pane>

        <el-tab-pane label="开放端口" name="ports" class="h-full flex flex-col">
           <div class="flex-1 overflow-y-auto custom-scrollbar p-0">
             <el-table :data="ports" style="width: 100%" class="glass-table" empty-text="暂无端口数据">
               <el-table-column prop="port_number" label="Port" width="120" sortable>
                 <template #default="{ row }">
                   <span class="text-blue-400 font-mono font-black text-lg">#{{ row.port_number }}</span>
                 </template>
               </el-table-column>
               <el-table-column prop="protocol" label="Protocol" width="100">
                 <template #default="{ row }">
                   <span class="uppercase text-xs font-bold text-slate-500 bg-slate-800 px-2 py-1 rounded">{{ row.protocol }}</span>
                 </template>
               </el-table-column>
               <el-table-column prop="service_name" label="Service" width="180">
                  <template #default="{ row }">
                    <span class="text-slate-200 font-medium">{{ row.service_name }}</span>
                  </template>
               </el-table-column>
               <el-table-column label="Product / Version">
                 <template #default="{ row }">
                   <div class="flex flex-col">
                     <span class="text-slate-300">{{ row.product || '-' }}</span>
                     <span v-if="row.version" class="text-slate-500 text-xs">{{ row.version }}</span>
                   </div>
                 </template>
               </el-table-column>
             </el-table>
           </div>
        </el-tab-pane>

      </el-tabs>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Globe, Connection, Lightning, Delete, MoreFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  fetchAssetById, 
  fetchAssetPorts, 
  fetchAssetVulns,
  triggerScan,
  deleteAsset,
  type Asset,
  type Port,
  type Vulnerability
} from '@/api/scan'

const route = useRoute()
const router = useRouter()
const assetId = Number(route.params.assetId)

// 状态管理
const activeTab = ref('vulns')
const scanning = ref(false)
const assetInfo = ref<Asset | null>(null)
const ports = ref<Port[]>([])
const vulns = ref<Vulnerability[]>([])

// 格式化日期
const formatDate = (str?: string) => {
  if (!str) return '-'
  return new Date(str).toLocaleString()
}

// 漏洞等级颜色映射
const getSeverityType = (sev: string) => {
  const s = sev.toLowerCase()
  if (['critical', 'high'].includes(s)) return 'danger'
  if (['medium'].includes(s)) return 'warning'
  if (['low'].includes(s)) return 'primary'
  return 'info'
}

// 加载所有数据
const loadData = async () => {
  if (!assetId) return
  try {
    const [assetRes, portRes, vulnRes] = await Promise.all([
      fetchAssetById(assetId),
      fetchAssetPorts(assetId),
      fetchAssetVulns(assetId)
    ])
    
    // 兼容逻辑：处理 ApiResponse 的解包问题
    // 如果拦截器已经解包，直接用；否则取 .data
    // 这里的 assetRes, portRes, vulnRes 可能是 { code: 200, data: ... } 也可能是 data 本身
    const getVal = (res: any) => res.data !== undefined ? res.data : res

    assetInfo.value = getVal(assetRes)
    ports.value = getVal(portRes) || []
    vulns.value = getVal(vulnRes) || []

    // 智能切换：如果无漏洞但有端口，优先展示端口
    if (vulns.value.length === 0 && ports.value.length > 0) {
      activeTab.value = 'ports'
    }
  } catch (e) {
    ElMessage.error('无法加载资产详情，资产可能已被删除')
    router.push('/assets')
  }
}

// 重新扫描逻辑
const handleRescan = async () => {
  scanning.value = true
  try {
    // 使用默认策略 'discovery'
    await triggerScan({ asset_id: assetId, strategy_name: 'discovery' })
    ElMessage.success('扫描任务已提交')
    router.push('/tasks')
  } catch (e: any) {
    ElMessage.error(e.message || '启动失败')
  } finally {
    scanning.value = false
  }
}

// 下拉菜单操作
const handleCommand = (command: string) => {
  if (command === 'delete') {
    handleDelete()
  }
}

// 删除资产
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      '此操作将永久删除该资产及其所有扫描记录。是否继续？',
      '警告',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        customClass: 'glass-message-box'
      }
    )
    await deleteAsset(assetId)
    ElMessage.success('资产已删除')
    router.push('/assets')
  } catch (e) {
    // 取消或出错
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
/* 动画 */
.fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* Tabs 样式深度定制 (适配 Glassmorphism) */
:deep(.glass-tabs .el-tabs__header) {
  margin: 0;
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
:deep(.glass-tabs .el-tabs__nav-wrap::after) { display: none; }
:deep(.glass-tabs .el-tabs__item) {
  color: #94a3b8;
  height: 56px;
  line-height: 56px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
}
:deep(.glass-tabs .el-tabs__item:hover) { color: #e2e8f0; }
:deep(.glass-tabs .el-tabs__item.is-active) {
  color: #38bdf8;
  font-weight: bold;
  text-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
}
:deep(.glass-tabs .el-tabs__content) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

/* 表格样式深度定制 */
:deep(.glass-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(30, 41, 59, 0.6);
  --el-table-border-color: rgba(255, 255, 255, 0.05);
  --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.05);
  --el-table-text-color: #cbd5e1;
  --el-table-header-text-color: #e2e8f0;
}
:deep(.el-table__inner-wrapper::before) { display: none; }
:deep(.el-table__empty-text) { color: #64748b; }
</style>