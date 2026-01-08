<template>
  <div class="h-full w-full fade-in flex flex-col gap-4 p-4 md:p-6 overflow-hidden">
    
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
            <span>Created: {{ formatDate(assetInfo?.created_at) }}</span>
          </p>
        </div>
      </div>

      <div class="flex items-center gap-4 self-end md:self-auto">
        <div class="hidden lg:flex gap-2 mr-2">
           <div class="stat-badge bg-blue-500/10 text-blue-400 border-blue-500/20">
             <span class="font-bold">{{ hosts.length }}</span> <span class="text-[10px] opacity-70">SUBS</span>
           </div>
           <div class="stat-badge bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
             <span class="font-bold">{{ webServices.length }}</span> <span class="text-[10px] opacity-70">WEB</span>
           </div>
           <div class="stat-badge bg-red-500/10 text-red-400 border-red-500/20">
             <span class="font-bold">{{ vulns.length }}</span> <span class="text-[10px] opacity-70">VULNS</span>
           </div>
        </div>

        <el-divider direction="vertical" class="border-slate-700 h-8 mx-0" />

        <div class="flex gap-2">
           <el-button type="primary" :icon="Lightning" @click="handleRescan" :loading="scanning">
             深度扫描
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
        
        <el-tab-pane name="hosts" class="h-full flex flex-col">
          <template #label>
            <span class="flex items-center gap-2"><el-icon><Files /></el-icon> 子域名 ({{ hosts.length }})</span>
          </template>
          
          <div class="flex-1 overflow-y-auto custom-scrollbar p-0">
             <el-table :data="hosts" style="width: 100%" class="glass-table" :row-class-name="tableRowClassName">
               <el-table-column prop="hostname" label="Hostname" min-width="200">
                 <template #default="{ row }">
                   <span class="font-mono text-slate-200 font-medium">{{ row.hostname }}</span>
                 </template>
               </el-table-column>
               
               <el-table-column label="IP Resolution" min-width="180">
                 <template #default="{ row }">
                   <div v-if="row.ips && row.ips.length" class="flex flex-wrap gap-1">
                     <span v-for="ip in row.ips" :key="ip" 
                           class="text-xs bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700">
                       {{ ip }}
                     </span>
                   </div>
                   <span v-else class="text-slate-600 italic text-xs">Unresolved</span>
                 </template>
               </el-table-column>

               <el-table-column prop="status" label="Status" width="120">
                  <template #default="{ row }">
                    <div class="flex items-center gap-2">
                      <span class="w-1.5 h-1.5 rounded-full" 
                            :class="row.status === 'confirmed' ? 'bg-emerald-500' : 'bg-slate-500'"></span>
                      <span class="capitalize text-slate-400 text-xs">{{ row.status }}</span>
                    </div>
                  </template>
               </el-table-column>
             </el-table>
          </div>
        </el-tab-pane>

        <el-tab-pane name="web" class="h-full flex flex-col">
          <template #label>
            <span class="flex items-center gap-2"><el-icon><Monitor /></el-icon> Web服务 ({{ webServices.length }})</span>
          </template>

          <div class="flex-1 overflow-y-auto custom-scrollbar p-4 bg-slate-900/20">
            <div class="grid grid-cols-1 gap-3">
              <div v-for="web in webServices" :key="web.id" 
                   class="group bg-slate-800/40 hover:bg-slate-800/60 border border-slate-700/50 hover:border-slate-600 rounded-lg p-4 transition-all flex flex-col md:flex-row gap-4">
                
                <div class="hidden md:block w-1 rounded-full self-stretch" 
                     :class="getStatusCodeColor(web.status, 'bg')"></div>

                <div class="flex-1 min-w-0">
                  <div class="flex items-start justify-between gap-4 mb-2">
                    <div class="flex items-center gap-3 min-w-0">
                       <span class="px-2 py-0.5 rounded text-xs font-black font-mono"
                             :class="getStatusCodeColor(web.status, 'badge')">
                         {{ web.status || '---' }}
                       </span>
                       <a :href="web.url" target="_blank" class="text-lg font-bold text-slate-200 hover:text-blue-400 truncate hover:underline font-mono">
                         {{ web.url }}
                       </a>
                    </div>
                  </div>

                  <h3 class="text-slate-400 text-sm mb-3 truncate" :title="web.title">
                    {{ web.title || 'No Title' }}
                  </h3>

                  <div class="flex flex-wrap gap-2 items-center">
                    <el-tooltip content="Web Server / Technology" placement="top" :show-after="500">
                       <el-icon class="text-slate-500"><Cpu /></el-icon>
                    </el-tooltip>
                    
                    <template v-if="web.tech && Object.keys(web.tech || {}).length">
                       <span v-for="(ver, name) in web.tech" :key="name" 
                             class="tech-tag text-xs px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300">
                         {{ name }} <span v-if="ver" class="text-slate-500 ml-1">{{ ver }}</span>
                       </span>
                    </template>
                    <span v-else class="text-xs text-slate-600 italic">Unknown Tech</span>
                  </div>
                </div>

                <div class="flex flex-col gap-2 justify-center border-l border-slate-700/50 pl-4 ml-2">
                  <el-button size="small" text bg icon="Link" @click="openLink(web.url)">Visit</el-button>
                </div>
              </div>
              
              <div v-if="webServices.length === 0" class="text-center py-10 text-slate-500">
                暂无 Web 服务数据，请确保已运行 httpx 探活任务
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane name="vulns" class="h-full flex flex-col">
           <template #label>
            <span class="flex items-center gap-2">
              <el-icon :class="vulns.length ? 'text-red-400' : ''"><Warning /></el-icon> 
              漏洞风险 ({{ vulns.length }})
            </span>
          </template>
           <div class="flex-1 overflow-y-auto custom-scrollbar p-0">
             <el-table :data="vulns" style="width: 100%" class="glass-table" empty-text="暂无漏洞数据">
               <el-table-column label="Severity" width="100" sortable prop="severity">
                 <template #default="{ row }">
                   <el-tag size="small" effect="dark" :type="getSeverityType(row.severity)" class="border-none font-bold">
                     {{ row.severity?.toUpperCase() }}
                   </el-tag>
                 </template>
               </el-table-column>
               
               <el-table-column prop="name" label="Vulnerability" min-width="250">
                  <template #default="{ row }">
                    <span class="font-bold text-slate-200">{{ row.name }}</span>
                    <div class="text-xs text-slate-500 mt-0.5">{{ row.template_id }}</div>
                  </template>
               </el-table-column>
               
               <el-table-column prop="url" label="Location" min-width="300" show-overflow-tooltip>
                 <template #default="{ row }">
                   <span class="text-slate-400 font-mono text-xs">{{ row.url }}</span>
                 </template>
               </el-table-column>
             </el-table>
           </div>
        </el-tab-pane>

        <el-tab-pane name="ports" class="h-full flex flex-col">
          <template #label>
            <span class="flex items-center gap-2"><el-icon><Connection /></el-icon> 端口 ({{ ports.length }})</span>
          </template>
           <div class="flex-1 overflow-y-auto custom-scrollbar p-0">
             <el-table :data="ports" style="width: 100%" class="glass-table">
               <el-table-column prop="port" label="Port" width="120" sortable>
                 <template #default="{ row }">
                   <span class="text-blue-400 font-mono font-black text-lg">#{{ row.port }}</span>
                 </template>
               </el-table-column>
               <el-table-column prop="ip" label="IP Address" width="180" />
               <el-table-column prop="service" label="Service">
                  <template #default="{ row }">
                    <span class="text-slate-200 font-medium">{{ row.service }}</span>
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
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  Globe, Connection, Lightning, Delete, MoreFilled, 
  Files, Monitor, Warning, Link, Cpu 
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  fetchAssetById, 
  fetchAssetPorts, 
  fetchAssetVulns,
  fetchAssetHosts,    // 需在 api/scan.ts 定义
  fetchAssetWeb,      // 需在 api/scan.ts 定义
  triggerScan,
  deleteAsset,
  type Asset,
  type Port,
  type Host,
  type WebService
} from '@/api/scan'

const route = useRoute()
const router = useRouter()
const assetId = Number(route.params.assetId)

// 状态管理
const activeTab = ref('hosts') // 默认看子域名
const scanning = ref(false)
const assetInfo = ref<Asset | null>(null)
const hosts = ref<Host[]>([])
const webServices = ref<WebService[]>([])
const ports = ref<Port[]>([])
const vulns = ref<any[]>([])

// 格式化日期
const formatDate = (str?: string) => {
  if (!str) return '-'
  return new Date(str).toLocaleDateString()
}

// 状态码颜色逻辑
const getStatusCodeColor = (code: number, type: 'bg' | 'badge') => {
  if (!code) return type === 'bg' ? 'bg-slate-700' : 'bg-slate-700 text-slate-400'
  
  if (code >= 200 && code < 300) {
    return type === 'bg' ? 'bg-emerald-500' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
  }
  if (code >= 300 && code < 400) {
    return type === 'bg' ? 'bg-blue-500' : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
  }
  if (code >= 400 && code < 500) {
    return type === 'bg' ? 'bg-orange-500' : 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
  }
  return type === 'bg' ? 'bg-red-500' : 'bg-red-500/20 text-red-400 border border-red-500/30'
}

const getSeverityType = (sev: string) => {
  if (!sev) return 'info'
  const s = sev.toLowerCase()
  if (['critical', 'high'].includes(s)) return 'danger'
  if (['medium'].includes(s)) return 'warning'
  if (['low'].includes(s)) return 'primary'
  return 'info'
}

// 辅助功能
const openLink = (url: string) => {
  window.open(url, '_blank')
}

// 加载数据
const loadData = async () => {
  if (!assetId) return
  try {
    // 并行请求所有数据
    // 注意：后端 results.py 的分页默认是 limit=100。
    // 这里为了演示效果，我们假设 params: { limit: 1000 } 来获取大部分数据
    const [assetRes, hostRes, webRes, portRes, vulnRes] = await Promise.all([
      fetchAssetById(assetId),
      fetchAssetHosts(assetId, { limit: 500 }),
      fetchAssetWeb(assetId, { limit: 500 }),
      fetchAssetPorts(assetId, { limit: 500 }),
      fetchAssetVulns(assetId, { limit: 500 })
    ])
    
    // API 响应解包辅助函数
    const getData = (res: any) => res.data?.items || res.data || res

    assetInfo.value = assetRes.data || assetRes
    hosts.value = getData(hostRes) || []
    webServices.value = getData(webRes) || []
    ports.value = getData(portRes) || []
    vulns.value = getData(vulnRes) || []

    // 智能 Tab 切换逻辑
    if (vulns.value.length > 0) activeTab.value = 'vulns'
    else if (webServices.value.length > 0) activeTab.value = 'web'
    else activeTab.value = 'hosts'

  } catch (e) {
    console.error(e)
    ElMessage.error('加载资产数据失败')
  }
}

const handleRescan = async () => {
  scanning.value = true
  try {
    await triggerScan({ asset_id: assetId, strategy_name: 'discovery' })
    ElMessage.success('扫描任务已提交')
    router.push('/tasks')
  } catch (e: any) {
    ElMessage.error(e.message || '启动失败')
  } finally {
    scanning.value = false
  }
}

const handleCommand = (command: string) => {
  if (command === 'delete') handleDelete()
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除该资产吗？', '警告', {
      type: 'warning',
      customClass: 'glass-message-box'
    })
    await deleteAsset(assetId)
    ElMessage.success('已删除')
    router.push('/assets')
  } catch {}
}

const tableRowClassName = ({ rowIndex }: { rowIndex: number }) => {
  return rowIndex % 2 === 0 ? 'bg-transparent' : 'bg-slate-800/20'
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* 统计小徽章 */
.stat-badge {
  @apply px-3 py-1 rounded-lg border flex flex-col items-center justify-center min-w-[60px] cursor-default select-none;
}

/* Tabs 深度定制 */
:deep(.glass-tabs .el-tabs__header) {
  margin: 0;
  background: rgba(15, 23, 42, 0.6);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding: 0 16px;
}
:deep(.glass-tabs .el-tabs__nav-wrap::after) { display: none; }
:deep(.glass-tabs .el-tabs__item) {
  color: #94a3b8;
  height: 48px;
  line-height: 48px;
  font-weight: 500;
  transition: all 0.3s;
}
:deep(.glass-tabs .el-tabs__item:hover) { color: #e2e8f0; }
:deep(.glass-tabs .el-tabs__item.is-active) { color: #38bdf8; font-weight: bold; }
:deep(.glass-tabs .el-tabs__content) { flex: 1; min-height: 0; display: flex; flex-direction: column; }

/* 表格定制 */
:deep(.glass-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(30, 41, 59, 0.4);
  --el-table-border-color: rgba(255, 255, 255, 0.05);
  --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.08);
  --el-table-text-color: #cbd5e1;
  --el-table-header-text-color: #94a3b8;
}
:deep(.el-table__inner-wrapper::before) { display: none; }
:deep(.el-table__empty-text) { color: #64748b; background: transparent; }

/* 滚动条 */
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }
</style>