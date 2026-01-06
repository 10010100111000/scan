<template>
  <div class="min-h-[80vh] flex flex-col items-center justify-center px-4 relative overflow-hidden">
    
    <div class="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
      <div class="absolute top-[20%] left-[20%] w-72 h-72 bg-blue-500/10 rounded-full blur-3xl"></div>
      <div class="absolute bottom-[20%] right-[20%] w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>
    </div>

    <div class="w-full max-w-2xl text-center z-10">
      <h1 class="text-4xl md:text-5xl font-extrabold text-gray-900 dark:text-white mb-6 tracking-tight">
        What do you want to <span class="text-blue-600">scan</span>?
      </h1>
      <p class="text-gray-500 dark:text-gray-400 mb-10 text-lg">
        输入域名、IP 或 CIDR。系统将自动检测目标是否存在。
      </p>

      <div class="relative group">
        <div class="relative flex items-center shadow-2xl rounded-2xl bg-white dark:bg-gray-800 border-2 border-transparent transition-all duration-300 focus-within:border-blue-500 focus-within:ring-4 focus-within:ring-blue-500/10">
          <div class="pl-6 text-gray-400">
            <el-icon :size="24"><Search /></el-icon>
          </div>
          <input 
            v-model="target"
            @keydown.enter="handleAction"
            type="text" 
            class="w-full h-16 bg-transparent border-none outline-none text-xl px-4 text-gray-900 dark:text-white placeholder-gray-400"
            placeholder="scanme.sh"
            autofocus
          />
          <div class="pr-2">
            <el-button 
              type="primary" 
              size="large" 
              class="!h-12 !px-8 !text-lg !rounded-xl"
              :loading="loading"
              @click="handleAction"
            >
              Scan
            </el-button>
          </div>
        </div>
      </div>

      <div class="mt-8 flex flex-wrap justify-center gap-4 animate-fade-in-up">
        
        <el-popover 
          placement="bottom" 
          :width="300" 
          trigger="click" 
          :visible="projPopoverVisible"
          @update:visible="projPopoverVisible = $event"
          @hide="resetInlineCreate"
        >
          <template #reference>
            <div class="config-chip cursor-pointer" @click="projPopoverVisible = !projPopoverVisible">
              <el-icon><Folder /></el-icon>
              <span class="max-w-[150px] truncate">项目: {{ currentProjectName }}</span>
              <el-icon class="ml-1"><ArrowDown /></el-icon>
            </div>
          </template>
          
          <div class="p-2">
            <div v-if="isCreatingProject" class="flex flex-col gap-2 animate-fade-in">
               <div class="text-xs text-gray-400 font-medium px-1">新建项目</div>
               <el-input 
                 ref="newProjectInputRef"
                 v-model="newProjectName" 
                 placeholder="输入项目名称..." 
                 size="default"
                 @keyup.enter="handleInlineCreate"
               />
               <div class="flex justify-end gap-2 mt-1">
                 <el-button size="small" text @click="isCreatingProject = false">取消</el-button>
                 <el-button 
                   size="small" 
                   type="primary" 
                   :loading="createLoading" 
                   :disabled="!newProjectName.trim()"
                   @click="handleInlineCreate"
                 >
                   创建
                 </el-button>
               </div>
            </div>

            <div v-else class="flex flex-col h-full">
              <div class="text-xs text-gray-400 mb-2 px-1">切换项目</div>
              <div class="max-h-56 overflow-y-auto custom-scrollbar">
                <div 
                  v-for="p in projects" :key="p.id"
                  @click="selectProject(p.id)"
                  class="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer flex justify-between items-center transition-colors group"
                  :class="{'bg-blue-50 dark:bg-blue-900/30 text-blue-600': selectedProjectId === p.id}"
                >
                  <span class="truncate font-medium text-sm">{{ p.name }}</span>
                  <el-icon v-if="selectedProjectId === p.id"><Check /></el-icon>
                </div>
              </div>
              <div class="border-t dark:border-gray-700 mt-2 pt-2">
                 <el-button text bg size="small" class="w-full justify-start" @click="switchToCreateMode">
                    <el-icon class="mr-1"><Plus /></el-icon> 新建项目
                 </el-button>
              </div>
            </div>
          </div>
        </el-popover>

        <el-popover placement="bottom" :width="350" trigger="click">
          <template #reference>
            <div class="config-chip cursor-pointer">
              <el-icon><Lightning /></el-icon>
              <span>策略: {{ currentStrategyLabel }}</span>
              <el-icon class="ml-1"><ArrowDown /></el-icon>
            </div>
          </template>
          <div class="p-2">
            <div class="text-xs text-gray-400 mb-2 px-1">选择扫描强度</div>
            <div class="space-y-2 max-h-[300px] overflow-y-auto custom-scrollbar">
               <div 
                v-for="s in strategies" :key="s.value"
                @click="selectedStrategy = s.value"
                class="p-3 border rounded-lg cursor-pointer hover:border-blue-500 hover:shadow-sm transition-all"
                :class="{'border-blue-500 bg-blue-50 dark:bg-blue-900/20': selectedStrategy === s.value}"
               >
                 <div class="font-bold text-sm text-gray-800 dark:text-gray-200">{{ s.label }}</div>
                 <div class="text-xs text-gray-500 mt-1 leading-relaxed">{{ s.desc }}</div>
               </div>
            </div>
          </div>
        </el-popover>

      </div>
    </div>

    <div class="mt-16 text-center z-10">
      <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">最近目标</p>
      <div class="flex flex-wrap justify-center gap-2">
        <span v-for="tag in recentTargets" :key="tag" class="px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded-full text-xs text-gray-600 dark:text-gray-300 cursor-pointer hover:bg-gray-200 transition-colors" @click="target = tag; handleAction()">
          {{ tag }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { Search, Folder, Lightning, ArrowDown, Check, Plus } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

// --- 核心引入：与最新的 api/scan.ts 保持一致 ---
import { 
  fetchProjects,
  searchAssetsByName,     // [Search]
  triggerScan,            // [Scan]
  createAsset,            // [Create Asset]
  createProject,
  fetchScanStrategies,
  type ScanStrategySummary 
} from '@/api/scan'

const router = useRouter()
const loading = ref(false)
const target = ref('')

// --- 项目数据 ---
const projects = ref<any[]>([])
const selectedProjectId = ref<number | null>(null)
const projPopoverVisible = ref(false)

// --- 新建项目状态 ---
const isCreatingProject = ref(false)
const newProjectName = ref('')
const createLoading = ref(false)
const newProjectInputRef = ref()

// --- 策略数据 ---
interface UIStrategy { value: string; label: string; desc: string }
const strategies = ref<UIStrategy[]>([])
const selectedStrategy = ref('') 

const recentTargets = ref(['example.com', 'scanme.nmap.org'])

// 计算属性
const currentProjectName = computed(() => {
  const p = projects.value.find(p => p.id === selectedProjectId.value)
  return p ? p.name : '默认项目'
})

const currentStrategyLabel = computed(() => {
  return strategies.value.find(s => s.value === selectedStrategy.value)?.label || '选择策略'
})

// 初始化加载
onMounted(async () => {
  try {
    const [projRes, stratRes] = await Promise.all([
      fetchProjects(),
      fetchScanStrategies()
    ])

    // 处理项目 (兼容数组或对象返回)
    // 根据最新的 api/scan.ts，request 会直接返回 T (即 Project[])，但为了稳健保留校验
    const list = Array.isArray(projRes) ? projRes : (projRes['data'] || [])
    projects.value = list
    
    // 默认选中 Default 或 第一个
    const defaultProj = list.find((p: any) => p.name === 'Default')
    if (defaultProj) {
      selectedProjectId.value = defaultProj.id
    } else if (list.length > 0) {
      selectedProjectId.value = list[0].id
    }

    // 处理策略
    const stratList = Array.isArray(stratRes) ? stratRes : (stratRes['data'] || [])
    strategies.value = stratList.map((s: ScanStrategySummary) => ({
      value: s.strategy_name,
      label: formatStrategyName(s.strategy_name),
      desc: s.description || s.steps.join(' -> ')
    }))
    if (strategies.value.length > 0) {
      selectedStrategy.value = strategies.value[0].value
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('初始化数据失败')
  }
})

// --- 项目交互逻辑 (内嵌式新建) ---
const switchToCreateMode = () => {
  isCreatingProject.value = true
  nextTick(() => {
    newProjectInputRef.value?.focus()
  })
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

// --- 核心动作逻辑：Search First, Then Scan ---
const handleAction = async () => {
  const input = target.value.trim()
  if (!input) return ElMessage.warning('请输入目标')
  if (!selectedProjectId.value) return ElMessage.warning('请选择一个项目')
  if (!selectedStrategy.value) return ElMessage.warning('请选择扫描策略')

  loading.value = true

  try {
    // 1. [Search 阶段] 全局查找
    const existRes = await searchAssetsByName(input) 
    
    // 兼容处理
    const existAssets = Array.isArray(existRes) ? existRes : (existRes['items'] || existRes['data'] || [])
    const exactMatch = existAssets.find((a: any) => a.name === input)

    if (exactMatch) {
      // 场景 A: 找到了 -> 跳转详情 (Lookup/Read)
      const fromProject = exactMatch.project_name ? ` (位于: ${exactMatch.project_name})` : ''
      ElMessage.success(`资产已存在${fromProject}，跳转查看...`)
      router.push(`/results/${exactMatch.id}`)
    } else {
      // 场景 B: 没找到 -> 新建并扫描 (Create + Scan)
      
      // 判断类型
      const isCidr = input.includes('/') || /^\d+\.\d+\.\d+\.\d+$/.test(input)
      const type = isCidr ? 'cidr' : 'domain'

      // 2. [Create Asset] 使用新签名: (projectId, payload)
      const newAsset = await createAsset(selectedProjectId.value, { 
        name: input, 
        type: type 
      })

      // 3. [Scan] 使用新签名: (payload)
      await triggerScan({
        asset_id: newAsset.id,
        strategy_name: selectedStrategy.value
      })
      
      ElMessage.success(`新扫描任务已启动`)
      router.push('/tasks')
    }
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e.message || '操作失败')
  } finally {
    loading.value = false
  }
}

const formatStrategyName = (rawName: string) => {
  if (rawName.includes('快速')) return '⚡ ' + rawName.replace(/^\d+\.\s*/, '')
  if (rawName.includes('深度')) return '🐢 ' + rawName.replace(/^\d+\.\s*/, '')
  if (rawName.includes('漏洞')) return '🔥 ' + rawName.replace(/^\d+\.\s*/, '')
  return rawName
}
</script>

<style scoped>
/* 胶囊样式 */
.config-chip {
  @apply flex items-center px-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-full 
         text-sm font-medium text-gray-600 dark:text-gray-300 border border-transparent
         hover:bg-gray-200 dark:hover:bg-gray-700 hover:border-gray-300 dark:hover:border-gray-600 
         transition-all select-none;
}

.config-chip .el-icon {
  @apply mr-1.5;
}

/* 简单的入场动画 */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in-up {
  animation: fadeInUp 0.6s ease-out forwards;
}

.animate-fade-in {
  animation: fadeIn 0.2s ease-out forwards;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 自定义滚动条 */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 4px;
}
.dark .custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #475569;
}
</style>