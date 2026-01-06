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
        输入域名、IP 或 CIDR。如果资产已存在，我们将直接带你查看详情。
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
        
        <el-popover placement="bottom" :width="300" trigger="click">
          <template #reference>
            <div class="config-chip cursor-pointer">
              <el-icon><Folder /></el-icon>
              <span>项目: {{ currentProjectName }}</span>
              <el-icon class="ml-1"><ArrowDown /></el-icon>
            </div>
          </template>
          <div class="p-2">
            <div class="text-xs text-gray-400 mb-2">切换项目</div>
            <div class="max-h-48 overflow-y-auto space-y-1">
              <div 
                v-for="p in projects" :key="p.id"
                @click="selectedProjectId = p.id"
                class="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer flex justify-between items-center"
                :class="{'bg-blue-50 text-blue-600': selectedProjectId === p.id}"
              >
                <span>{{ p.name }}</span>
                <el-icon v-if="selectedProjectId === p.id"><Check /></el-icon>
              </div>
            </div>
            <div class="border-t mt-2 pt-2">
               <el-button text bg size="small" class="w-full" @click="showCreateProject = true">+ 新建项目</el-button>
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
            <div class="text-xs text-gray-400 mb-2">选择扫描强度</div>
            <div class="space-y-2">
               <div 
                v-for="s in strategies" :key="s.value"
                @click="selectedStrategy = s.value"
                class="p-3 border rounded-lg cursor-pointer hover:border-blue-500 transition-colors"
                :class="{'border-blue-500 bg-blue-50 dark:bg-blue-900/20': selectedStrategy === s.value}"
               >
                 <div class="font-bold text-sm">{{ s.label }}</div>
                 <div class="text-xs text-gray-500 mt-1">{{ s.desc }}</div>
               </div>
            </div>
          </div>
        </el-popover>

      </div>
    </div>

    <div class="mt-16 text-center z-10">
      <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">最近目标</p>
      <div class="flex flex-wrap justify-center gap-2">
        <span v-for="tag in recentTargets" :key="tag" class="px-3 py-1 bg-gray-100 dark:bg-gray-800 rounded-full text-xs text-gray-600 dark:text-gray-300 cursor-pointer hover:bg-gray-200" @click="target = tag; handleAction()">
          {{ tag }}
        </span>
      </div>
    </div>

    <ProjectCreateDialog v-model="showCreateProject" @success="onProjectCreated" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search, Folder, Lightning, ArrowDown, Check, Plus } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import ProjectCreateDialog from '@/components/ProjectCreateDialog.vue'
// 1. 引入获取策略的 API
import { 
  getProjects, 
  submitScan, 
  getAssets, 
  fetchScanStrategies, 
  type ScanStrategySummary 
} from '@/api/scan'

const router = useRouter()
const loading = ref(false)
const target = ref('')
const showCreateProject = ref(false)

// 数据状态
const projects = ref<any[]>([])
const selectedProjectId = ref<number | null>(null)

// 2. 将 strategies 定义为空数组，等待 API 加载
// 我们定义一个适配 UI 的接口
interface UIStrategy {
  value: string
  label: string
  desc: string
}
const strategies = ref<UIStrategy[]>([])
const selectedStrategy = ref('') 

const recentTargets = ref(['example.com', 'scanme.nmap.org'])

const currentProjectName = computed(() => {
  const p = projects.value.find(p => p.id === selectedProjectId.value)
  return p ? p.name : '默认项目'
})

const currentStrategyLabel = computed(() => {
  // 从加载好的列表中查找
  return strategies.value.find(s => s.value === selectedStrategy.value)?.label || '选择策略'
})

// 初始化
onMounted(async () => {
  try {
    // 并行请求：获取项目 + 获取策略
    const [projRes, stratRes] = await Promise.all([
      getProjects(),
      fetchScanStrategies()
    ])

    // --- A. 处理项目 ---
    const list = projRes.data || projRes
    projects.value = list
    const defaultProj = list.find((p: any) => p.name === 'Default')
    if (defaultProj) {
      selectedProjectId.value = defaultProj.id
    } else if (list.length > 0) {
      selectedProjectId.value = list[0].id
    }

    // --- B. 处理策略 (关键修改) ---
    // 将后端返回的 ScanStrategySummary 转换为 UI 需要的格式
    strategies.value = stratRes.map((s: ScanStrategySummary) => ({
      value: s.strategy_name,  // 传给后端的值
      label: formatStrategyName(s.strategy_name), // 美化后的显示名
      desc: s.description || s.steps.join(' -> ') // 描述
    }))

    // 默认选中第一个策略
    if (strategies.value.length > 0) {
      selectedStrategy.value = strategies.value[0].value
    }

  } catch (e) {
    ElMessage.error('初始化数据失败，请检查后端服务')
  }
})

// 辅助函数：美化策略名称 (可选)
// 把 "1. 域名快速侦察 (Web)" 变成更短的 "⚡ 域名快速侦察"
const formatStrategyName = (rawName: string) => {
  if (rawName.includes('快速')) return '⚡ ' + rawName.replace(/^\d+\.\s*/, '')
  if (rawName.includes('深度')) return '🐢 ' + rawName.replace(/^\d+\.\s*/, '')
  if (rawName.includes('漏洞')) return '🔥 ' + rawName.replace(/^\d+\.\s*/, '')
  return rawName
}

const handleAction = async () => {
  const input = target.value.trim()
  if (!input) return ElMessage.warning('请输入目标')
  if (!selectedProjectId.value) return ElMessage.warning('请选择一个项目')
  if (!selectedStrategy.value) return ElMessage.warning('请选择扫描策略')

  loading.value = true

  try {
    const existRes = await getAssets(selectedProjectId.value, { search: input, limit: 1 })
    // 注意：这里的 existRes 可能需要根据你实际 API 返回结构调整 (res.data 或 res.items)
    const existAssets = Array.isArray(existRes) ? existRes : (existRes.items || existRes.data || [])
    
    const exactMatch = existAssets.find((a: any) => a.name === input)

    if (exactMatch) {
      ElMessage.success(`资产 ${input} 已存在，正在跳转...`)
      router.push(`/results/${exactMatch.id}`) // 跳转到结果页
    } else {
      await submitScan({
        project_id: selectedProjectId.value,
        asset_name: input,
        strategy_name: selectedStrategy.value // 这里使用的是真实的后端策略名
      })
      ElMessage.success(`目标 ${input} 扫描已启动`)
      router.push('/tasks')
    }
  } catch (e: any) {
    console.error(e)
    ElMessage.error(e.message || '操作失败')
  } finally {
    loading.value = false
  }
}

const onProjectCreated = (newProject: any) => {
  projects.value.unshift(newProject)
  selectedProjectId.value = newProject.id
}
</script>

<style scoped>
/* 胶囊样式：类似 Notion/Linear 的 Tag */
.config-chip {
  @apply flex items-center px-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-full 
         text-sm font-medium text-gray-600 dark:text-gray-300
         hover:bg-gray-200 dark:hover:bg-gray-700 transition-all select-none;
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
</style>