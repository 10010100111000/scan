<template>
  <section class="dashboard-main fade-in">
    <header class="dashboard-header card-glass mb-4">
      <div>
        <p class="text-faint text-xs font-bold uppercase tracking-widest mb-1">Command Center</p>
        <h2 class="hero-title text-2xl text-slate-100">攻击面概览</h2>
        <p class="text-faint text-sm mt-1">
          当前纳管资产 <span class="text-blue-400 font-bold">{{ stats.kpi.assets_total }}</span> 个，
          今日已完成扫描 <span class="text-emerald-400 font-bold">{{ stats.kpi.tasks_completed_today }}</span> 次
        </p>
      </div>
      <div class="flex items-center gap-4">
        <div class="text-right hidden sm:block">
          <div class="text-sm font-bold text-slate-200">{{ userInfo?.username }}</div>
          <div class="text-xs text-slate-500">{{ userInfo?.roles?.[0] || 'Admin' }}</div>
        </div>
        <el-avatar class="bg-gradient-to-br from-blue-500 to-indigo-600 font-bold">
          {{ userInfo?.username?.[0]?.toUpperCase() }}
        </el-avatar>
      </div>
    </header>

    <section class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
      <div v-for="(kpi, i) in kpiCards" :key="i" 
           class="card-glass p-5 rounded-2xl flex items-center gap-4 hover:bg-white/5 transition-all cursor-default group">
        <div class="w-12 h-12 rounded-xl flex items-center justify-center text-xl shadow-lg group-hover:scale-110 transition-transform"
             :style="{ background: kpi.bg, color: kpi.color }">
          <el-icon><component :is="kpi.icon" /></el-icon>
        </div>
        <div>
          <p class="text-xs text-slate-400 mb-0.5">{{ kpi.title }}</p>
          <div class="flex items-baseline gap-2">
            <span class="text-2xl font-bold text-slate-100 tracking-tight">{{ kpi.value }}</span>
            <span v-if="kpi.sub" class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/50">
              {{ kpi.sub }}
            </span>
          </div>
        </div>
      </div>
    </section>

    <section class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4 h-[380px]">
      <div class="card-glass lg:col-span-2 p-5 rounded-2xl flex flex-col relative overflow-hidden">
        <div class="flex justify-between items-center mb-2 z-10">
          <div>
            <h3 class="font-bold text-slate-200">近 7 天活跃度</h3>
            <p class="text-xs text-slate-500">扫描任务执行趋势</p>
          </div>
          <div class="flex gap-2">
            <span class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
            <span class="text-xs text-blue-400">Live</span>
          </div>
        </div>
        <div class="flex-1 w-full min-h-0">
          <v-chart class="chart" :option="trendOption" autoresize />
        </div>
      </div>

      <div class="card-glass p-5 rounded-2xl flex flex-col relative">
        <div class="mb-2 z-10">
          <h3 class="font-bold text-slate-200">风险分布</h3>
          <p class="text-xs text-slate-500">漏洞等级占比</p>
        </div>
        <div class="flex-1 w-full min-h-0 relative">
          <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span class="text-3xl font-black text-slate-100">{{ vulnTotal }}</span>
            <span class="text-xs text-slate-500">Total</span>
          </div>
          <v-chart class="chart" :option="vulnOption" autoresize />
        </div>
      </div>
    </section>

    <section class="card-glass p-5 rounded-2xl">
      <div class="flex justify-between items-center mb-4">
        <div class="flex items-center gap-2">
          <h3 class="font-bold text-slate-200">最新纳管资产</h3>
          <el-tag size="small" effect="dark" round type="primary">{{ stats.lists.recent_assets.length }} New</el-tag>
        </div>
        <el-button text size="small" @click="$router.push('/assets')">查看全部 <el-icon class="ml-1"><ArrowRight /></el-icon></el-button>
      </div>
      
      <el-table 
        :data="stats.lists.recent_assets" 
        style="width: 100%" 
        class="glass-table"
      >
        <el-table-column prop="name" label="资产名称" min-width="200">
          <template #default="{ row }">
            <span class="font-medium text-slate-200">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" :type="row.type === 'domain' ? '' : 'warning'">
              {{ row.type.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="发现时间" align="right" width="180">
          <template #default="{ row }">
            <span class="text-slate-400 text-xs font-mono">{{ new Date(row.created_at).toLocaleString() }}</span>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { Monitor, Timer, DataLine, Warning, ArrowRight } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { fetchDashboardStats, type DashboardStats } from '@/api/scan'

// ECharts 核心组件引入
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'

// 注册组件
use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent])

const auth = useAuthStore()
const userInfo = computed(() => auth.userInfo)
const loading = ref(true)

// 初始空状态数据
const stats = reactive<DashboardStats>({
  kpi: { assets_total: 0, assets_domains: 0, tasks_running: 0, tasks_pending: 0, tasks_completed_today: 0 },
  charts: { trend_dates: [], trend_values: [], vuln_distribution: [] },
  lists: { recent_assets: [] }
})

// 计算 KPI 卡片配置 (响应式)
const kpiCards = computed(() => [
  {
    title: '在线资产',
    value: stats.kpi.assets_total,
    sub: `${stats.kpi.assets_domains} Domains`,
    icon: Monitor,
    bg: 'rgba(16, 185, 129, 0.15)', color: '#34d399' // Emerald
  },
  {
    title: '正在扫描',
    value: stats.kpi.tasks_running,
    icon: Timer,
    bg: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa' // Blue
  },
  {
    title: '待处理任务',
    value: stats.kpi.tasks_pending,
    icon: DataLine,
    bg: 'rgba(251, 191, 36, 0.15)', color: '#fbbf24' // Amber
  },
  {
    title: '今日完成',
    value: stats.kpi.tasks_completed_today,
    icon: Warning, // 暂时复用图标，可更换
    bg: 'rgba(168, 85, 247, 0.15)', color: '#c084fc' // Purple
  }
])

// 计算漏洞总数
const vulnTotal = computed(() => {
  return stats.charts.vuln_distribution.reduce((acc, cur) => acc + cur.value, 0)
})

// ECharts 配置：趋势图
const trendOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: { 
    trigger: 'axis',
    backgroundColor: 'rgba(15, 23, 42, 0.9)',
    borderColor: '#334155',
    textStyle: { color: '#e2e8f0' }
  },
  grid: { top: 10, right: 10, bottom: 20, left: 0, containLabel: true },
  xAxis: {
    type: 'category',
    data: stats.charts.trend_dates,
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#64748b', fontSize: 11 }
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#334155', type: 'dashed', opacity: 0.3 } },
    axisLabel: { color: '#64748b', fontSize: 11 }
  },
  series: [{
    data: stats.charts.trend_values,
    type: 'line',
    smooth: true,
    showSymbol: false,
    lineStyle: { width: 3, color: '#38bdf8' },
    areaStyle: {
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(56, 189, 248, 0.4)' }, 
          { offset: 1, color: 'rgba(56, 189, 248, 0)' }
        ]
      }
    }
  }]
}))

// ECharts 配置：环形图
const vulnOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: { trigger: 'item' },
  legend: { 
    bottom: 0, 
    itemWidth: 8, itemHeight: 8,
    textStyle: { color: '#94a3b8', fontSize: 11 } 
  },
  color: ['#ef4444', '#f97316', '#eab308', '#3b82f6'], // 红橙黄蓝
  series: [{
    type: 'pie',
    radius: ['55%', '75%'],
    center: ['50%', '42%'],
    avoidLabelOverlap: false,
    itemStyle: { 
      borderRadius: 4, 
      borderColor: '#1e293b', 
      borderWidth: 2 
    },
    label: { show: false },
    data: stats.charts.vuln_distribution
  }]
}))

onMounted(async () => {
  try {
    const res = await fetchDashboardStats()
    Object.assign(stats, res)
  } catch (e) {
    console.error('Failed to load dashboard stats', e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.chart {
  height: 100%;
  width: 100%;
}

.fade-in {
  animation: fadeIn 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 表格穿透样式：去背景、改边框 */
.glass-table {
  --el-table-bg-color: transparent !important;
  --el-table-tr-bg-color: transparent !important;
  --el-table-header-bg-color: rgba(255, 255, 255, 0.03) !important;
  --el-table-border-color: rgba(255, 255, 255, 0.05) !important;
  --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.05) !important;
  --el-table-text-color: #cbd5e1 !important;
  --el-table-header-text-color: #94a3b8 !important;
  background: transparent !important;
}

/* 隐藏表格底部的白线 */
:deep(.el-table__inner-wrapper::before) {
  display: none;
}
</style>