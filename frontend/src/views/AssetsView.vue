<template>
  <div class="flex h-full gap-4 fade-in">
    
    <aside class="w-72 flex flex-col gap-4">
      <div class="card-glass p-4 rounded-2xl">
        <div class="text-xs text-slate-400 uppercase font-bold tracking-wider mb-2">Total Assets</div>
        <div class="text-3xl font-black text-slate-100 mb-1">{{ globalStats.total }}</div>
        <div class="flex gap-2 text-xs">
          <span class="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
            {{ globalStats.domains }} Domains
          </span>
          <span class="px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
            {{ globalStats.cidrs }} CIDRs
          </span>
        </div>
      </div>

      <div class="card-glass flex-1 rounded-2xl overflow-hidden flex flex-col">
        <div class="p-4 border-b border-slate-700/50 flex justify-between items-center bg-slate-800/20">
          <span class="font-bold text-slate-300">Projects</span>
          <el-button link type="primary" size="small" @click="openCreateProject">
            <el-icon><Plus /></el-icon>
          </el-button>
        </div>
        
        <div class="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-1">
          <div class="project-item" :class="{ 'active': selectedProjectId === null }" @click="selectedProjectId = null">
            <el-icon><Menu /></el-icon><span class="flex-1">全部资产</span>
          </div>
          <div v-for="p in projects" :key="p.id" class="project-item" :class="{ 'active': selectedProjectId === p.id }" @click="selectedProjectId = p.id">
            <el-icon><Folder /></el-icon><span class="flex-1 truncate">{{ p.name }}</span>
          </div>
        </div>
      </div>
    </aside>

    <main class="flex-1 flex flex-col gap-4 min-w-0">
      <div class="card-glass p-4 rounded-2xl flex justify-between items-center">
        <div class="flex items-center gap-3">
          <div class="text-lg font-bold text-slate-200">{{ currentProjectName }}</div>
          <el-divider direction="vertical" class="border-slate-600" />
          <el-input 
            v-model="searchQuery" 
            placeholder="搜索资产..." 
            :prefix-icon="Search" 
            class="w-64 glass-input" 
            clearable 
            @change="fetchData" 
          />
          <el-radio-group v-model="typeFilter" size="small" class="glass-radio" @change="fetchData">
            <el-radio-button label="all">All</el-radio-button>
            <el-radio-button label="domain">Domains</el-radio-button>
            <el-radio-button label="cidr">CIDRs</el-radio-button>
          </el-radio-group>
        </div>
        <el-button type="primary" color="#3b82f6" class="shadow-lg shadow-blue-500/20" @click="openCreateAsset">
          <el-icon class="mr-1"><Plus /></el-icon> 添加资产
        </el-button>
      </div>

      <div class="card-glass flex-1 rounded-2xl overflow-hidden relative">
        <el-table 
          :data="assetList" 
          style="width: 100%; height: 100%" 
          class="glass-table absolute inset-0"
          v-loading="loading"
        >
          <el-table-column width="60" align="center">
            <template #default="{ row }">
              <div class="flex justify-center">
                <div class="w-8 h-8 rounded-lg flex items-center justify-center text-lg"
                     :class="row.type === 'domain' ? 'bg-blue-500/10 text-blue-400' : 'bg-purple-500/10 text-purple-400'">
                  <el-icon><component :is="row.type === 'domain' ? 'Globe' : 'Connection'" /></el-icon>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="Asset Name" min-width="200">
            <template #default="{ row }">
              <div class="flex flex-col cursor-pointer group" @click="goToResults(row)">
                <span class="font-bold text-slate-200 group-hover:text-blue-400 transition-colors">{{ row.name }}</span>
                <span class="text-xs text-slate-500">{{ new Date(row.created_at).toLocaleDateString() }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="Project" width="150" v-if="selectedProjectId === null">
             <template #default="{ row }">
               <span class="text-xs px-2 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                 {{ getProjectName(row.project_id) }}
               </span>
             </template>
          </el-table-column>

          <el-table-column align="right" width="180">
            <template #default="{ row }">
              <div class="flex justify-end gap-2 opacity-80 hover:opacity-100">
                 <el-tooltip content="扫描" placement="top" effect="light">
                    <el-button circle size="small" type="primary" plain @click.stop="quickScan(row)">
                      <el-icon><Lightning /></el-icon>
                    </el-button>
                 </el-tooltip>
                 
                 <el-tooltip content="删除" placement="top" effect="light">
                    <el-button circle size="small" type="danger" plain @click.stop="handleDelete(row)">
                       <el-icon><Delete /></el-icon>
                    </el-button>
                 </el-tooltip>
              </div>
            </template>
          </el-table-column>

          <template #empty><el-empty description="暂无资产" :image-size="100" /></template>
        </el-table>
      </div>
    </main>

    <el-dialog v-model="createVisible" title="添加/查找资产" width="400px" class="glass-dialog" align-center>
      <el-form label-position="top">
        <el-form-item label="所属项目">
           <el-select v-model="formProjectId" placeholder="选择项目" class="w-full">
              <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
           </el-select>
        </el-form-item>
        <el-form-item label="资产目标">
          <el-input v-model="formTargets" type="textarea" :rows="4" placeholder="example.com&#10;192.168.1.0/24" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createVisible = false">取消</el-button>
          <el-button type="primary" :loading="creating" @click="submitCreate">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog v-model="createProjectVisible" title="新建项目" width="300px" class="glass-dialog" align-center>
       <el-input v-model="newProjectName" placeholder="项目名称" @keyup.enter="submitCreateProject" />
       <template #footer>
          <el-button type="primary" class="w-full" @click="submitCreateProject" :loading="projectCreating">创建</el-button>
       </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Menu, Folder, Plus, Search, Globe, Connection, Lightning, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  fetchProjects, 
  fetchAssets, 
  createAsset, 
  createProject, 
  triggerScan, 
  deleteAsset, 
  type Asset, 
  type Project 
} from '@/api/scan'

const router = useRouter()
const loading = ref(false)
const projects = ref<Project[]>([])
const assetList = ref<Asset[]>([])

const selectedProjectId = ref<number | null>(null)
const searchQuery = ref('')
const typeFilter = ref('all')

const createVisible = ref(false)
const creating = ref(false)
const formProjectId = ref<number | null>(null)
const formTargets = ref('')
const createProjectVisible = ref(false)
const projectCreating = ref(false)
const newProjectName = ref('')

const globalStats = computed(() => ({
  total: assetList.value.length,
  domains: assetList.value.filter(a => a.type === 'domain').length,
  cidrs: assetList.value.filter(a => a.type === 'cidr').length
}))

const currentProjectName = computed(() => {
  if (selectedProjectId.value === null) return 'All Assets'
  const p = projects.value.find(p => p.id === selectedProjectId.value)
  return p ? p.name : 'Unknown Project'
})

// [Core] 获取数据：后端支持分页和筛选
const fetchData = async () => {
  loading.value = true
  try {
    const params: any = { limit: 100 }
    if (selectedProjectId.value) params.project_id = selectedProjectId.value
    if (typeFilter.value !== 'all') params.type = typeFilter.value
    if (searchQuery.value) params.search = searchQuery.value

    const res = await fetchAssets(params)
    // 兼容处理：如果拦截器解包了 ApiResponse，res 就是数组
    // 如果没有解包，res.data 才是数组
    const list = Array.isArray(res) ? res : (res['data'] || [])
    assetList.value = list
  } catch (e) {
    ElMessage.error('加载资产失败')
  } finally {
    loading.value = false
  }
}

watch([selectedProjectId, typeFilter], () => { fetchData() })

const initAll = async () => {
  try {
    const pRes = await fetchProjects({ limit: 100 })
    projects.value = Array.isArray(pRes) ? pRes : (pRes['data'] || [])
    fetchData()
  } catch(e) { console.error(e) }
}

const getProjectName = (pid: number) => {
  return projects.value.find(p => p.id === pid)?.name || 'Unknown'
}

const openCreateProject = () => {
  newProjectName.value = ''
  createProjectVisible.value = true
}

const submitCreateProject = async () => {
  if (!newProjectName.value.trim()) return
  projectCreating.value = true
  try {
    const res = await createProject({ name: newProjectName.value })
    projects.value.push(res) // res 应该是 Project 对象
    ElMessage.success('项目创建成功')
    createProjectVisible.value = false
    selectedProjectId.value = res.id
  } catch (e: any) {
    ElMessage.error(e.message)
  } finally {
    projectCreating.value = false
  }
}

const openCreateAsset = () => {
  formProjectId.value = selectedProjectId.value || (projects.value.length > 0 ? projects.value[0].id : null)
  formTargets.value = ''
  createVisible.value = true
}

const submitCreate = async () => {
  if (!formProjectId.value || !formTargets.value.trim()) return ElMessage.warning('请补全信息')
  creating.value = true
  
  const lines = formTargets.value.split('\n').map(s => s.trim()).filter(s => s)
  let successCount = 0
  let lastId = null

  for (const target of lines) {
    try {
      const isCidr = target.includes('/') || /^\d+\.\d+\.\d+\.\d+$/.test(target)
      const type = isCidr ? 'cidr' : 'domain'
      // 后端返回 Asset 对象（可能是新创建的，也可能是旧的）
      const asset = await createAsset(formProjectId.value, { name: target, type })
      lastId = asset.id
      successCount++
    } catch (e) { console.error(e) }
  }

  createVisible.value = false
  creating.value = false
  
  if (lines.length === 1 && lastId) {
    ElMessage.success('跳转到资产详情...')
    router.push({ name: 'Results', params: { assetId: lastId } })
  } else {
    ElMessage.success(`处理完成`)
    fetchData()
  }
}

const quickScan = async (row: Asset) => {
  try {
    await triggerScan({ asset_id: row.id, strategy_name: 'discovery' }) 
    ElMessage.success(`已发起扫描`)
    router.push('/tasks')
  } catch (e: any) { ElMessage.error('启动失败: ' + e.message) }
}

const handleDelete = async (row: Asset) => {
  try {
    await ElMessageBox.confirm(`确定要删除 ${row.name} 吗？`, '警告', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消'
    })
    await deleteAsset(row.id)
    ElMessage.success('已删除')
    fetchData()
  } catch (e) {}
}

const goToResults = (row: Asset) => {
  router.push({ name: 'Results', params: { assetId: row.id } })
}

onMounted(() => { initAll() })
</script>

<style scoped>
.fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
.project-item { @apply flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-all text-slate-400 hover:text-slate-100 hover:bg-white/5 border border-transparent select-none group; }
.project-item.active { @apply bg-blue-600/20 text-blue-400 border-blue-500/30 font-bold; }
:deep(.glass-table) { --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; --el-table-header-bg-color: rgba(30, 41, 59, 0.4); --el-table-border-color: rgba(255,255,255,0.05); --el-table-row-hover-bg-color: rgba(255,255,255,0.05); --el-table-text-color: #94a3b8; --el-table-header-text-color: #e2e8f0; }
:deep(.el-table__inner-wrapper::before) { display: none; }
:deep(.glass-input .el-input__wrapper) { background-color: rgba(15, 23, 42, 0.5) !important; box-shadow: 0 0 0 1px rgba(71, 85, 105, 0.5) !important; }
:deep(.glass-input .el-input__wrapper.is-focus) { box-shadow: 0 0 0 1px #3b82f6 !important; }
</style>