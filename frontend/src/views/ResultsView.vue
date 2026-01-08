<template>
  <div class="h-full w-full bg-[#0f172a] flex flex-col overflow-hidden relative">
    
    <header class="shrink-0 h-16 border-b border-white/5 flex items-center px-4 justify-between bg-[#0f172a]/50 backdrop-blur-md z-20">
      <div class="flex items-center gap-4 flex-1">
        <div class="flex items-center gap-2 text-sm font-medium text-slate-400">
          <router-link to="/assets" class="hover:text-white transition-colors">Assets</router-link>
          <el-icon><ArrowRight /></el-icon>
          <span class="text-slate-100 flex items-center gap-2">
            <el-icon v-if="assetInfo?.type === 'domain'" class="text-blue-400"><ChromeFilled /></el-icon>
            {{ assetInfo?.name }}
          </span>
        </div>

        <div class="h-4 w-px bg-white/10 mx-2"></div>

        <div class="flex-1 max-w-xl relative group">
          <el-icon class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400"><Search /></el-icon>
          <input 
            type="text" 
            v-model="searchQuery"
            placeholder="Filter results (e.g. status=200)..." 
            class="w-full bg-[#1e293b]/50 border border-white/10 rounded-md py-1.5 pl-9 pr-4 text-sm text-slate-200 focus:outline-none focus:border-blue-500/50 focus:bg-[#1e293b] transition-all placeholder:text-slate-600"
          />
        </div>
      </div>

      <div class="flex items-center gap-3">
         <button 
           @click="handleRescan"
           class="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded shadow-lg shadow-blue-900/20 transition-all border border-blue-400/20"
         >
           <el-icon :class="{ 'is-loading': scanning }"><Refresh /></el-icon>
           {{ scanning ? 'Scanning...' : 'Rescan' }}
         </button>
      </div>
    </header>

    <div class="flex-1 flex overflow-hidden">
      
      <nav class="w-16 flex flex-col items-center py-4 gap-4 border-r border-white/5 bg-[#0f172a] shrink-0">
         <button 
           v-for="tab in tabs" 
           :key="tab.id"
           @click="activeTab = tab.id"
           class="w-10 h-10 rounded-xl flex items-center justify-center text-xl transition-all relative group"
           :class="activeTab === tab.id ? 'bg-blue-500/20 text-blue-400' : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'"
         >
           <el-icon><component :is="tab.icon" /></el-icon>
           
           <span v-if="tab.count" class="absolute -top-1 -right-1 flex h-4 min-w-[16px] px-0.5 items-center justify-center rounded-full bg-[#0f172a] text-[9px] font-bold text-slate-400 border border-white/10 z-10">
             {{ tab.count > 99 ? '99+' : tab.count }}
           </span>
           
           <div class="absolute left-full ml-3 px-2 py-1 bg-slate-800 border border-white/10 rounded text-xs text-white opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-50 transition-opacity shadow-xl">
             {{ tab.label }}
           </div>
         </button>
      </nav>

      <main class="flex-1 overflow-y-auto custom-scrollbar bg-[#0f172a] p-0 relative">
        
        <div v-if="activeTab === 'web'" class="flex flex-col min-w-[800px]">
           <div class="sticky top-0 z-10 grid grid-cols-12 gap-4 px-6 py-3 border-b border-white/5 bg-[#0f172a]/95 backdrop-blur text-xs font-bold text-slate-500 uppercase tracking-wider">
              <div class="col-span-5">Target</div>
              <div class="col-span-3">Tech Stack</div>
              <div class="col-span-2">Status</div>
              <div class="col-span-2 text-right">Action</div>
           </div>

           <div 
             v-for="item in webServices" 
             :key="item.id"
             @click="openDrawer(item)"
             class="group grid grid-cols-12 gap-4 px-6 py-3 border-b border-white/[0.02] hover:bg-white/[0.02] cursor-pointer transition-colors items-center relative"
             :class="{ 'bg-blue-500/[0.05]': selectedAsset?.id === item.id }"
           >
              <div v-if="selectedAsset?.id === item.id" class="absolute left-0 top-0 bottom-0 w-[3px] bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>

              <div class="col-span-5 min-w-0">
                 <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded bg-slate-800/50 border border-white/5 flex items-center justify-center shrink-0 text-slate-500 group-hover:border-white/20 transition-colors">
                       <el-icon size="14"><ChromeFilled /></el-icon>
                    </div>
                    <div class="min-w-0 flex-1">
                       <div class="text-sm font-medium text-slate-200 truncate font-mono hover:text-blue-400 transition-colors">
                          {{ item.url }}
                       </div>
                       <div class="text-xs text-slate-500 truncate mt-0.5">
                          {{ item.title || 'No title' }}
                       </div>
                    </div>
                 </div>
              </div>

              <div class="col-span-3">
                 <div class="flex flex-wrap gap-1.5 h-6 overflow-hidden mask-image-b">
                    <span v-for="(ver, name) in item.tech || {}" :key="name" 
                          class="px-1.5 py-px rounded-[4px] border border-white/10 bg-[#1e293b]/50 text-[10px] text-slate-400 flex items-center hover:border-slate-500 transition-colors">
                       {{ name }}
                    </span>
                    <span v-if="!item.tech" class="text-slate-700 text-xs">-</span>
                 </div>
              </div>

              <div class="col-span-2">
                 <div class="flex items-center gap-2">
                    <div class="w-1.5 h-1.5 rounded-full" :class="getStatusColor(item.status, 'bg')"></div>
                    <span class="text-xs font-mono font-medium" :class="getStatusColor(item.status, 'text')">
                       {{ item.status || 'ERR' }}
                    </span>
                 </div>
              </div>

              <div class="col-span-2 text-right opacity-0 group-hover:opacity-100 transition-opacity">
                 <el-button link size="small" @click.stop="openLink(item.url)">
                    <el-icon><Link /></el-icon>
                 </el-button>
              </div>
           </div>

           <div v-if="webServices.length === 0" class="flex flex-col items-center justify-center py-20 text-slate-500">
              <el-icon size="48" class="mb-4 opacity-20"><Monitor /></el-icon>
              <p>No web services found</p>
           </div>
        </div>
        
        <div v-if="activeTab === 'hosts'" class="flex flex-col min-w-[800px]">
           <div class="sticky top-0 z-10 grid grid-cols-12 gap-4 px-6 py-3 border-b border-white/5 bg-[#0f172a]/95 backdrop-blur text-xs font-bold text-slate-500 uppercase tracking-wider">
              <div class="col-span-6">Hostname</div>
              <div class="col-span-4">Resolution</div>
              <div class="col-span-2 text-right">Status</div>
           </div>
           
           <div v-for="host in hosts" :key="host.id" 
                class="grid grid-cols-12 gap-4 px-6 py-3 border-b border-white/[0.02] hover:bg-white/[0.02] items-center">
              <div class="col-span-6 font-mono text-sm text-slate-300">{{ host.hostname }}</div>
              <div class="col-span-4 flex flex-wrap gap-2">
                 <span v-for="ip in host.ips" :key="ip" class="px-1.5 rounded bg-slate-800 text-slate-400 text-xs border border-white/5">{{ ip }}</span>
              </div>
              <div class="col-span-2 text-right text-xs text-slate-500 uppercase">{{ host.status }}</div>
           </div>
        </div>

      </main>
    </div>

    <AssetDrawer 
      :visible="!!selectedAsset" 
      :asset="selectedAsset || {}"
      @close="selectedAsset = null"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { 
  ChromeFilled, // [修复] 已替换 Globe
  Monitor, Files, Warning, ArrowRight, Search, 
  Refresh, Link 
} from '@element-plus/icons-vue'
import AssetDrawer from '@/components/AssetDrawer.vue'
import { fetchAssetById, fetchAssetWeb, fetchAssetHosts } from '@/api/scan'

const route = useRoute()
const assetId = Number(route.params.assetId)

// Data
const assetInfo = ref<any>(null)
const webServices = ref<any[]>([])
const hosts = ref<any[]>([]) // 新增 hosts 数据
const activeTab = ref('web')
const selectedAsset = ref<any>(null)
const scanning = ref(false)
const searchQuery = ref('')

// Tabs Config
const tabs = computed(() => [
  { id: 'hosts', label: 'Subdomains', icon: Files, count: hosts.value.length },
  { id: 'web', label: 'Web Services', icon: Monitor, count: webServices.value.length },
  { id: 'vulns', label: 'Vulnerabilities', icon: Warning, count: 0 },
])

// Helpers
const openDrawer = (item: any) => {
  selectedAsset.value = item
}

const getStatusColor = (code: number, type: 'bg' | 'text') => {
  if (!code) return type === 'bg' ? 'bg-slate-700' : 'text-slate-500'
  if (code >= 200 && code < 300) return type === 'bg' ? 'bg-emerald-500' : 'text-emerald-400'
  if (code >= 300 && code < 400) return type === 'bg' ? 'bg-blue-500' : 'text-blue-400'
  if (code >= 400 && code < 500) return type === 'bg' ? 'bg-orange-500' : 'text-orange-400'
  return type === 'bg' ? 'bg-red-500' : 'text-red-400'
}

const openLink = (url: string) => window.open(url, '_blank')
const handleRescan = () => { /* 逻辑 */ }

// Init
onMounted(async () => {
  if (!assetId) return
  try {
    const [assetRes, webRes, hostRes] = await Promise.all([
      fetchAssetById(assetId),
      fetchAssetWeb(assetId, { limit: 500 }),
      fetchAssetHosts(assetId, { limit: 500 }) // 同时加载子域名
    ])
    
    assetInfo.value = assetRes.data || assetRes
    webServices.value = webRes.items || []
    hosts.value = hostRes.items || []
  } catch (e) {
    console.error(e)
  }
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 8px; }
.custom-scrollbar::-webkit-scrollbar-track { background: #0f172a; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; border: 2px solid #0f172a; }
</style>