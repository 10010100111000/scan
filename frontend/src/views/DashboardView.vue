<template>
  <div class="h-full w-full fade-in p-6 overflow-y-auto">
    <header class="flex justify-between items-end mb-8">
      <div>
        <h1 class="text-3xl font-black text-slate-100 tracking-tight">Command Center</h1>
        <p class="text-slate-400 mt-2">
          全网资产 <span class="text-blue-400 font-mono font-bold">{{ stats.assets }}</span> 个，
          发现高危漏洞 <span class="text-red-400 font-mono font-bold">{{ stats.vulns_high }}</span> 个
        </p>
      </div>
      <el-button type="primary" size="large" :icon="Plus" @click="$router.push('/scan')">
        新建任务
      </el-button>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div v-for="(card, i) in kpiCards" :key="i" class="card-glass p-6 rounded-2xl relative overflow-hidden group">
        <div class="absolute -right-6 -top-6 w-24 h-24 rounded-full opacity-10 transition-transform group-hover:scale-110" 
             :style="{ background: card.color }"></div>
        
        <div class="relative z-10">
          <div class="flex items-center gap-3 mb-3 text-slate-400">
            <el-icon :size="20"><component :is="card.icon" /></el-icon>
            <span class="text-xs font-bold uppercase tracking-wider">{{ card.title }}</span>
          </div>
          <div class="text-3xl font-black text-slate-100 font-mono">
            {{ card.value }}
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="card-glass lg:col-span-2 p-6 rounded-2xl flex flex-col h-[400px]">
        <h3 class="font-bold text-slate-200 mb-6 flex items-center gap-2">
          <el-icon class="text-blue-400"><TrendCharts /></el-icon> 扫描活跃度
        </h3>
        <div class="flex-1 w-full min-h-0">
          <v-chart class="chart" :option="trendOption" autoresize />
        </div>
      </div>

      <div class="card-glass p-6 rounded-2xl flex flex-col h-[400px]">
        <h3 class="font-bold text-slate-200 mb-6 flex items-center gap-2">
          <el-icon class="text-red-400"><Warning /></el-icon> 风险分布
        </h3>
        <div class="flex-1 w-full min-h-0 relative">
          <v-chart class="chart" :option="vulnOption" autoresize />
          <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div class="text-center">
              <div class="text-3xl font-black text-slate-100">{{ stats.vulns_total }}</div>
              <div class="text-xs text-slate-500 uppercase">Vulns</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { Plus, Monitor, DataLine, Warning, TrendCharts, Timer } from '@element-plus/icons-vue'
import { fetchDashboardStats, type DashboardStats } from '@/api/scan'

// ECharts
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

// 状态
const loading = ref(true)
const stats = reactive({
  assets: 0,
  tasks_running: 0,
  tasks_pending: 0,
  vulns_high: 0,
  vulns_total: 0
})

const trendData = ref<{date: string, count: number}[]>([])
const vulnData = ref<{name: string, value: number}[]>([])

// KPI Cards
const kpiCards = computed(() => [
  { title: 'Total Assets', value: stats.assets, icon: Monitor, color: '#3b82f6' },
  { title: 'High Risks', value: stats.vulns_high, icon: Warning, color: '#ef4444' },
  { title: 'Running Tasks', value: stats.tasks_running, icon: Timer, color: '#eab308' },
  { title: 'Pending Tasks', value: stats.tasks_pending, icon: DataLine, color: '#64748b' }
])

// Chart Options
const trendOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,23,42,0.9)', borderColor: '#334155', textStyle: { color: '#e2e8f0' } },
  grid: { top: 10, right: 10, bottom: 20, left: 30, containLabel: true },
  xAxis: {
    type: 'category',
    data: trendData.value.map(i => i.date),
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#64748b' }
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#334155', type: 'dashed' } },
    axisLabel: { color: '#64748b' }
  },
  series: [{
    data: trendData.value.map(i => i.count),
    type: 'line',
    smooth: true,
    symbol: 'none',
    itemStyle: { color: '#3b82f6' },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: 'rgba(59,130,246,0.5)' }, { offset: 1, color: 'rgba(59,130,246,0)' }]
      }
    }
  }]
}))

const vulnOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, itemWidth: 8, itemHeight: 8, textStyle: { color: '#94a3b8' } },
  series: [{
    type: 'pie',
    radius: ['50%', '70%'],
    center: ['50%', '45%'],
    avoidLabelOverlap: false,
    itemStyle: { borderRadius: 4, borderColor: '#1e293b', borderWidth: 2 },
    label: { show: false },
    data: vulnData.value.length ? vulnData.value : [{ value: 0, name: 'No Data' }]
  }]
}))

// 初始化
const initData = async () => {
  try {
    // 假设后端有一个聚合接口 /stats/dashboard
    // 如果没有，你需要自己拼凑 fetchAssets, fetchTasks 等接口
    // 这里我们使用推荐的 fetchDashboardStats 接口
    const res = await fetchDashboardStats()
    
    // 赋值 KPI
    stats.assets = res.kpi.assets_total
    stats.tasks_running = res.kpi.tasks_running
    stats.tasks_pending = res.kpi.tasks_pending
    // 这里的 vulns_critical 是我们主要关注的高危
    stats.vulns_high = res.kpi.vulns_critical 
    
    // 赋值图表数据
    trendData.value = res.charts.trend_dates.map((d, i) => ({
      date: d,
      count: res.charts.trend_values[i]
    }))
    
    vulnData.value = res.charts.vuln_distribution
    stats.vulns_total = vulnData.value.reduce((acc, cur) => acc + cur.value, 0)

  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  initData()
})
</script>

<style scoped>
.chart { height: 100%; width: 100%; }
.fade-in { animation: fadeIn 0.5s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>