<template>
  <div class="h-full w-full fade-in p-6 overflow-y-auto custom-scrollbar">
    
    <div class="card-glass p-8 rounded-3xl mb-8 relative overflow-hidden flex flex-col md:flex-row justify-between items-center gap-6">
      <div class="absolute top-0 right-0 w-[400px] h-full bg-gradient-to-l from-blue-600/20 via-blue-900/10 to-transparent pointer-events-none"></div>
      <div class="absolute -right-10 -top-10 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div class="flex items-center gap-6 z-10 w-full md:w-auto">
        <div class="relative">
          <el-avatar :size="72" class="bg-gradient-to-br from-blue-500 to-purple-600 text-3xl font-black text-white border-4 border-white/5 shadow-2xl">
            {{ userInitial }}
          </el-avatar>
          <div class="absolute bottom-0 right-0 w-5 h-5 bg-green-500 border-4 border-[#0f172a] rounded-full"></div>
        </div>
        <div>
          <h2 class="text-3xl font-black text-slate-100 tracking-tight">
            Welcome back, <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">Admin</span>
          </h2>
          <div class="flex items-center gap-3 mt-2 text-slate-400 text-sm font-medium">
            <span class="flex items-center gap-1.5 bg-slate-800/50 px-2 py-1 rounded border border-slate-700/50">
              <el-icon class="text-blue-400"><Calendar /></el-icon> {{ currentDate }}
            </span>
            <span class="flex items-center gap-1.5 bg-slate-800/50 px-2 py-1 rounded border border-slate-700/50">
              <el-icon class="text-green-400"><CircleCheckFilled /></el-icon> System Online
            </span>
          </div>
        </div>
      </div>

      <div class="flex gap-8 z-10 border-t md:border-t-0 md:border-l border-slate-700/50 pt-4 md:pt-0 md:pl-8 w-full md:w-auto justify-around md:justify-end">
        <div class="text-center">
          <div class="text-xs text-slate-500 uppercase font-bold tracking-widest mb-1">Assets</div>
          <div class="text-2xl font-black text-slate-200">{{ stats.assets }}</div>
        </div>
        <div class="text-center">
          <div class="text-xs text-slate-500 uppercase font-bold tracking-widest mb-1">Vulns</div>
          <div class="text-2xl font-black text-red-400">{{ stats.vulns_high }}</div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div v-for="(card, i) in kpiCards" :key="i" class="card-glass p-5 rounded-2xl relative overflow-hidden group hover:-translate-y-1 transition-transform duration-300">
        <div class="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
        
        <div class="relative z-10 flex justify-between items-start">
          <div>
            <div class="text-slate-400 text-xs font-bold uppercase tracking-wider mb-2">{{ card.title }}</div>
            <div class="text-3xl font-black text-slate-100 font-mono">{{ card.value }}</div>
          </div>
          <div class="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50 text-slate-300 group-hover:text-white group-hover:scale-110 transition-all"
               :style="{ color: card.color }">
            <el-icon :size="24"><component :is="card.icon" /></el-icon>
          </div>
        </div>
        
        <div class="absolute bottom-0 left-0 w-full h-1 bg-slate-800">
          <div class="h-full transition-all duration-1000 ease-out" 
               :style="{ width: '60%', background: card.color }"></div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 pb-6">
      <div class="card-glass lg:col-span-2 p-6 rounded-2xl flex flex-col h-[420px]">
        <h3 class="font-bold text-slate-200 mb-6 flex items-center gap-2">
          <div class="w-1 h-5 bg-blue-500 rounded-full"></div>
          <span class="text-lg">Scan Activity</span>
        </h3>
        <div class="flex-1 w-full min-h-0">
          <v-chart class="chart" :option="trendOption" autoresize />
        </div>
      </div>

      <div class="card-glass p-6 rounded-2xl flex flex-col h-[420px]">
        <h3 class="font-bold text-slate-200 mb-6 flex items-center gap-2">
          <div class="w-1 h-5 bg-red-500 rounded-full"></div>
          <span class="text-lg">Risk Distribution</span>
        </h3>
        <div class="flex-1 w-full min-h-0 relative">
          <v-chart class="chart" :option="vulnOption" autoresize />
          
          <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none mt-2">
            <div class="text-4xl font-black text-slate-100">{{ stats.vulns_total }}</div>
            <div class="text-xs text-slate-500 uppercase font-bold tracking-widest mt-1">Total Issues</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { Monitor, DataLine, Warning, Timer, Calendar, CircleCheckFilled } from '@element-plus/icons-vue'
import { fetchDashboardStats } from '@/api/scan'

// ECharts
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

// User & Date Info
const userInitial = ref('A') // 这里可以接 store 获取真实用户名
const currentDate = new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })

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

// KPI Cards Configuration
const kpiCards = computed(() => [
  { title: 'Total Assets', value: stats.assets, icon: Monitor, color: '#3b82f6' }, // Blue
  { title: 'Critical / High', value: stats.vulns_high, icon: Warning, color: '#ef4444' }, // Red
  { title: 'Running Tasks', value: stats.tasks_running, icon: Timer, color: '#eab308' }, // Yellow
  { title: 'Pending Queue', value: stats.tasks_pending, icon: DataLine, color: '#64748b' } // Slate
])

// ECharts Options (保持之前的配置，稍微优化颜色)
const trendOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: { 
    trigger: 'axis', 
    backgroundColor: 'rgba(15,23,42,0.95)', 
    borderColor: '#334155', 
    textStyle: { color: '#e2e8f0' },
    padding: [10, 15]
  },
  grid: { top: 20, right: 20, bottom: 20, left: 40, containLabel: true },
  xAxis: {
    type: 'category',
    data: trendData.value.map(i => i.date),
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#64748b', margin: 15 }
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#334155', type: 'dashed', opacity: 0.5 } },
    axisLabel: { color: '#64748b' }
  },
  series: [{
    data: trendData.value.map(i => i.count),
    type: 'line',
    smooth: true,
    showSymbol: false,
    symbolSize: 8,
    itemStyle: { color: '#3b82f6', borderWidth: 2 },
    lineStyle: { width: 3, shadowColor: 'rgba(59,130,246,0.5)', shadowBlur: 10 },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: 'rgba(59,130,246,0.3)' }, { offset: 1, color: 'rgba(59,130,246,0)' }]
      }
    }
  }]
}))

const vulnOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: { trigger: 'item' },
  legend: { bottom: 0, itemWidth: 10, itemHeight: 10, textStyle: { color: '#94a3b8' } },
  series: [{
    type: 'pie',
    radius: ['60%', '75%'], // 甜甜圈更细一点，显得现代
    center: ['50%', '45%'],
    avoidLabelOverlap: false,
    itemStyle: { borderRadius: 6, borderColor: '#1e293b', borderWidth: 3 },
    label: { show: false },
    data: vulnData.value.length ? vulnData.value : [{ value: 0, name: 'No Data' }]
  }]
}))

const initData = async () => {
  try {
    const res: any = await fetchDashboardStats()
    const data = res.data || res
    
    if (data && data.kpi) {
      stats.assets = data.kpi.assets_total
      stats.tasks_running = data.kpi.tasks_running
      stats.tasks_pending = data.kpi.tasks_pending
      stats.vulns_high = data.kpi.vulns_critical
      
      trendData.value = data.charts.trend_dates.map((d: any, i: any) => ({
        date: d,
        count: data.charts.trend_values[i]
      }))
      
      // 给漏洞分布上色
      const colorMap: Record<string, string> = {
        'critical': '#ef4444',
        'high': '#f97316',
        'medium': '#eab308',
        'low': '#3b82f6',
        'info': '#64748b'
      }
      
      vulnData.value = data.charts.vuln_distribution.map((item: any) => ({
        ...item,
        itemStyle: { color: colorMap[item.name.toLowerCase()] || '#94a3b8' }
      }))
      
      stats.vulns_total = vulnData.value.reduce((acc, cur) => acc + cur.value, 0)
    }
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
.fade-in { animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1); }
@keyframes fadeIn { 
  from { opacity: 0; transform: translateY(10px) scale(0.98); } 
  to { opacity: 1; transform: translateY(0) scale(1); } 
}

/* 玻璃卡片增强 */
.card-glass {
  background: rgba(30, 41, 59, 0.4); /* 更深的底色 */
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
</style>