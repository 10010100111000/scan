<template>
  <div class="h-full w-full flex flex-col items-center relative isolate">
    
    <div class="absolute inset-0 overflow-hidden pointer-events-none z-0">
      <div class="absolute top-[-10%] left-[20%] w-[500px] h-[500px] bg-blue-600/20 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow"></div>
      <div class="absolute bottom-[-10%] right-[20%] w-[400px] h-[400px] bg-purple-600/20 rounded-full blur-[100px] mix-blend-screen animate-pulse-slow" style="animation-delay: 2s;"></div>
    </div>

    <div class="flex-1 w-full max-w-3xl px-6 z-10 flex flex-col items-center justify-center">
      
      <h1 class="text-4xl md:text-6xl font-black mb-4 tracking-tight text-center text-slate-200">
         <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-300">扫描控制台</span>
      </h1>
      <p class="text-slate-400 mb-12 text-lg md:text-xl font-light text-center max-w-xl mx-auto">
        输入域名、IP 或 CIDR。全网资产，一键触达。
      </p>

      <div class="w-full relative group">
        <div class="absolute -inset-1 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
        
        <div class="relative flex items-center bg-slate-900/80 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl transition-all duration-300 focus-within:border-blue-500/50 focus-within:ring-1 focus-within:ring-blue-500/50">
          <div class="pl-6 text-slate-400">
            <el-icon :size="24"><Search /></el-icon>
          </div>
          <input 
            v-model="target"
            @keydown.enter="handleAction"
            type="text" 
            class="w-full h-20 bg-transparent border-none outline-none text-2xl px-5 text-white placeholder-slate-600 font-medium"
            placeholder="example.com"
            autofocus
            spellcheck="false"
          />
          <div class="pr-3">
            <button 
              class="h-12 px-8 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-all shadow-lg shadow-blue-500/30 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="loading"
              @click="handleAction"
            >
              <span v-if="loading" class="animate-spin mr-2">⟳</span>
              <span>SCAN</span>
            </button>
          </div>
        </div>
      </div>

      <div class="mt-10 flex flex-wrap justify-center gap-4 animate-fade-in-up">
        
        <el-popover 
          placement="bottom" 
          :width="300" 
          trigger="click" 
          popper-class="glass-popover" 
          v-model:visible="projPopoverVisible"
        >
          <template #reference>
            <div class="config-chip">
              <el-icon class="text-blue-400"><Folder /></el-icon>
              <span class="truncate max-w-[120px]">{{ currentProjectName }}</span>
              <el-icon class="ml-2 text-slate-500 text-xs"><ArrowDown /></el-icon>
            </div>
          </template>
          
          <div class="p-2">
            <div v-show="isCreatingProject" class="flex flex-col gap-2 animate-fade-in">
               <div class="text-xs text-slate-400 font-medium px-1">新建项目</div>
               <el-input 
                 ref="newProjectInputRef"
                 v-model="newProjectName" 
                 placeholder="输入项目名称..." 
                 @keyup.enter="handleInlineCreate"
               />
               <div class="flex justify-end gap-2 mt-1">
                 <el-button size="small" text @click="isCreatingProject = false">取消</el-button>
                 <el-button size="small" type="primary" :loading="createLoading" @click="handleInlineCreate">创建</el-button>
               </div>
            </div>

            <div v-show="!isCreatingProject" class="flex flex-col h-full">
              <div class="text-xs text-slate-400 mb-2 px-1">切换项目</div>
              <div class="max-h-56 overflow-y-auto custom-scrollbar space-y-1">
                <div 
                  v-for="p in projects" :key="p.id"
                  @click="selectProject(p.id)"
                  class="p-2 rounded hover:bg-slate-700/50 cursor-pointer flex justify-between items-center transition-colors text-sm"
                  :class="{'bg-blue-500/10 text-blue-400': selectedProjectId === p.id}"
                >
                  <span class="truncate">{{ p.name }}</span>
                  <el-icon v-if="selectedProjectId === p.id"><Check /></el-icon>
                </div>
              </div>
              <div class="border-t border-slate-700 mt-2 pt-2">
                 <el-button text bg size="small" class="w-full justify-start" @click.stop="switchToCreateMode">
                    <el-icon class="mr-1"><Plus /></el-icon> 新建项目
                 </el-button>
              </div>
            </div>
          </div>
        </el-popover>

        <el-popover 
          placement="right" 
          :width="320" 
          trigger="click" 
          popper-class="glass-popover"
        >
          <template #reference>
            <div class="config-chip">
              <el-icon class="text-yellow-400"><Lightning /></el-icon>
              <span>{{ currentStrategyLabel }}</span>
              <el-icon class="ml-2 text-slate-500 text-xs"><ArrowRight /></el-icon>
            </div>
          </template>
          <div class="p-2">
            <div class="text-xs text-slate-400 mb-2 px-1">扫描强度</div>
            <div class="space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar">
               <div 
                v-for="s in strategies" :key="s.value"
                @click="selectedStrategy = s.value"
                class="p-3 border border-slate-700/50 rounded-lg cursor-pointer hover:border-blue-500/50 hover:bg-slate-800/50 transition-all"
                :class="{'border-blue-500 bg-blue-500/10': selectedStrategy === s.value}"
               >
                 <div class="font-bold text-sm text-slate-200">{{ s.label }}</div>
                 <div class="text-xs text-slate-500 mt-1">{{ s.desc }}</div>
               </div>
            </div>
          </div>
        </el-popover>

      </div>
    </div>

    <div class="w-full text-center z-10 pb-12 mt-auto">
      <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">RECENT TARGETS</p>
      <div class="flex flex-wrap justify-center gap-2 px-4">
        <span 
          v-for="tag in recentTargets" :key="tag" 
          class="px-3 py-1 bg-slate-800/50 border border-slate-700 rounded-full text-xs text-slate-400 cursor-pointer hover:bg-slate-700 hover:text-white transition-all hover:scale-105" 
          @click="target = tag; handleAction()"
        >
          {{ tag }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { Search, Folder, Lightning, ArrowDown, ArrowRight, Check, Plus } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

// [核心修改] 1. 引入 useScanOverlay 钩子
import { useScanOverlay } from '@/composables/useScanOverlay'

import { 
  fetchProjects,
  searchAssetsByName,     
  triggerScan,            
  createAsset,            
  createProject,
  fetchScanStrategies,
  type ScanStrategySummary 
} from '@/api/scan'

const router = useRouter()
// [核心修改] 2. 获取 close 方法
const { close: closeOverlay } = useScanOverlay()

const loading = ref(false)
const target = ref('')

const projects = ref<any[]>([])
const selectedProjectId = ref<number | null>(null)
const projPopoverVisible = ref(false)
const isCreatingProject = ref(false)
const newProjectName = ref('')
const createLoading = ref(false)
const newProjectInputRef = ref()

interface UIStrategy { value: string; label: string; desc: string }
const strategies = ref<UIStrategy[]>([])
const selectedStrategy = ref('') 

const recentTargets = ref(['example.com', 'scanme.nmap.org'])

const currentProjectName = computed(() => {
  const p = projects.value.find(p => p.id === selectedProjectId.value)
  return p ? p.name : 'Default'
})

const currentStrategyLabel = computed(() => {
  return strategies.value.find(s => s.value === selectedStrategy.value)?.label || 'Strategy'
})

watch(projPopoverVisible, (val) => {
  if (!val) {
    setTimeout(() => {
      resetInlineCreate()
    }, 200)
  }
})

onMounted(async () => {
  try {
    const [projRes, stratRes] = await Promise.all([
      fetchProjects(),
      fetchScanStrategies()
    ])
    const list = Array.isArray(projRes) ? projRes : (projRes['data'] || [])
    projects.value = list
    const defaultProj = list.find((p: any) => p.name === 'Default')
    if (defaultProj) selectedProjectId.value = defaultProj.id
    else if (list.length > 0) selectedProjectId.value = list[0].id

    const stratList = Array.isArray(stratRes) ? stratRes : (stratRes['data'] || [])
    strategies.value = stratList.map((s: ScanStrategySummary) => ({
      value: s.strategy_name,
      label: formatStrategyName(s.strategy_name),
      desc: s.description || s.steps.join(' -> ')
    }))
    if (strategies.value.length > 0) selectedStrategy.value = strategies.value[0].value
  } catch (e) {
    // Silent fail
  }
})

const switchToCreateMode = () => {
  isCreatingProject.value = true
  nextTick(() => { newProjectInputRef.value?.focus() })
}

const handleInlineCreate = async () => {
  const name = newProjectName.value.trim()
  if (!name) return
  createLoading.value = true
  try {
    const newProject = await createProject({ name })
    projects.value.unshift(newProject)
    selectedProjectId.value = newProject.id
    ElMessage.success('项目已创建')
    resetInlineCreate()
    projPopoverVisible.value = false
  } catch (e: any) {
    ElMessage.error(e.message || '创建项目失败')
  } finally {
    createLoading.value = false
  }
}

const resetInlineCreate = () => {
  isCreatingProject.value = false
  newProjectName.value = ''
}

const selectProject = (id: number) => {
  selectedProjectId.value = id
  projPopoverVisible.value = false
}

const handleAction = async () => {
  const input = target.value.trim()
  if (!input) return ElMessage.warning('请输入目标')

  loading.value = true

  try {
    // 智能初始化 Default
    if (!selectedProjectId.value) {
      try {
        let defaultProj = projects.value.find(p => p.name === 'Default')
        if (!defaultProj) {
           defaultProj = await createProject({ name: 'Default' })
           projects.value.unshift(defaultProj)
           ElMessage.success('已自动初始化 Default 项目')
        }
        selectedProjectId.value = defaultProj.id
      } catch (e) {
        loading.value = false
        return ElMessage.warning('请先创建一个项目')
      }
    }

    if (!selectedStrategy.value) {
      loading.value = false
      return ElMessage.warning('请选择扫描策略')
    }

    const existRes = await searchAssetsByName(input) 
    const existAssets = Array.isArray(existRes) ? existRes : (existRes['items'] || existRes['data'] || [])
    const exactMatch = existAssets.find((a: any) => a.name === input)

    if (exactMatch) {
      ElMessage.success(`资产已存在，跳转查看...`)
      
      // [核心修改] 3. 成功后，先关闭遮罩层
      closeOverlay()
      
      router.push(`/results/${exactMatch.id}`)
    } else {
      const isCidr = input.includes('/') || /^\d+\.\d+\.\d+\.\d+$/.test(input)
      const type = isCidr ? 'cidr' : 'domain'
      const newAsset = await createAsset(selectedProjectId.value!, { name: input, type: type })
      await triggerScan({ asset_id: newAsset.id, strategy_name: selectedStrategy.value })
      
      ElMessage.success(`扫描已启动`)
      
      // [核心修改] 3. 成功后，先关闭遮罩层
      closeOverlay()
      
      router.push('/tasks')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  } finally {
    loading.value = false
  }
}

const formatStrategyName = (rawName: string) => {
  if (rawName.includes('快速')) return '⚡ 快速侦察'
  if (rawName.includes('深度')) return '🐢 深度全扫'
  if (rawName.includes('漏洞')) return '🔥 漏洞扫描'
  return rawName
}
</script>

<style>
/* 玻璃风格 Popover */
.glass-popover.el-popover {
  background: rgba(15, 23, 42, 0.9) !important;
  backdrop-filter: blur(12px) !important;
  border: 1px solid rgba(51, 65, 85, 0.5) !important;
  color: #e2e8f0 !important;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5) !important;
}
.glass-popover .el-popper__arrow::before {
  background: rgba(15, 23, 42, 0.9) !important;
  border-color: rgba(51, 65, 85, 0.5) !important;
}
</style>

<style scoped>
.config-chip {
  @apply flex items-center px-4 py-2.5 rounded-full cursor-pointer select-none transition-all duration-200
         bg-slate-800/40 border border-slate-700/50 text-slate-300 text-sm font-medium
         hover:bg-slate-700/60 hover:border-slate-600 hover:text-white hover:scale-105 active:scale-95;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in-up {
  animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.animate-pulse-slow {
  animation: pulse 8s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .5; }
}

.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background-color: #334155; border-radius: 4px; }
</style>