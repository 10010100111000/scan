<template>
  <aside :class="['nav-rail', 'card-glass', { collapsed }]">
    <div class="nav-rail__top">
      <div class="brand" v-if="!collapsed">
        <p class="brand__eyebrow">SCAN · 控制</p>
        <h3>Attack Surface</h3>
      </div>
      <el-button circle size="small" @click="$emit('toggle')" aria-label="切换导航宽度">
        <el-icon>
          <component :is="collapsed ? Expand : Fold" />
        </el-icon>
      </el-button>
    </div>

    <el-button class="new-scan" type="primary" plain block @click="openScan">
      <el-icon><Plus /></el-icon>
      <span v-if="!collapsed">新建扫描</span>
    </el-button>

    <div class="nav-list">
      <router-link
        v-for="item in navLinks"
        :key="item.id"
        :to="item.route"
        :class="['nav-item', { active: isActive(item.route) }]"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span v-if="!collapsed">{{ item.label }}</span>
        <span v-if="item.id === 'tasks' && indicator !== 'idle'" class="task-indicator" :class="indicator">
          <span v-if="indicator === 'running'" class="task-spinner"></span>
          <span v-else class="task-dot"></span>
        </span>
      </router-link>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useRoute, useRouter, type RouteLocationRaw } from 'vue-router'
import { Compass, DataBoard, Expand, Fold, Monitor, Plus, Timer, User } from '@element-plus/icons-vue'
import { useScanOverlay } from '@/composables/useScanOverlay'
import { useTaskStatus } from '@/composables/useTaskStatus'
import type { Component } from 'vue'

defineProps<{ collapsed: boolean }>()
defineEmits<{ (event: 'toggle'): void }>()

const route = useRoute()
const router = useRouter()
const { open: openScan } = useScanOverlay()
const { indicator } = useTaskStatus()

const navLinks: Array<{ id: string; label: string; icon: Component; route: RouteLocationRaw }> = [
  { id: 'dashboard', label: '仪表盘', icon: DataBoard, route: { name: 'Dashboard' } },
  { id: 'tasks', label: '任务流', icon: Timer, route: { name: 'Tasks' } },
  { id: 'assets', label: '资产', icon: Monitor, route: { name: 'Assets' } },
  { id: 'setup', label: '初始化', icon: Compass, route: { name: 'Setup' } },
  { id: 'account', label: '账号', icon: User, route: { name: 'Login' } },
]

const isActive = (navRoute: RouteLocationRaw) => router.resolve(navRoute).href === route.fullPath
</script>

<style scoped>
.nav-rail {
  position: sticky;
  top: 16px;
  align-self: start;
  height: calc(100vh - 32px);
  padding: 16px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: width 0.2s ease, padding 0.2s ease;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
}

.nav-rail.collapsed {
  width: 100%;
  padding: 16px 12px;
}

.nav-rail__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.brand__eyebrow {
  margin: 0;
  letter-spacing: 0.08em;
  font-size: 12px;
  text-transform: uppercase;
  color: #94a3b8;
}

.brand h3 {
  margin: 4px 0 0;
}

.new-scan {
  justify-content: center;
}

.new-scan .el-icon {
  margin-right: 6px;
}

.nav-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  color: #cbd5e1;
  transition: background 0.2s ease, color 0.2s ease;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #e2e8f0;
}

.nav-item.active {
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.18), rgba(99, 102, 241, 0.08));
  color: #f8fafc;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.nav-rail.collapsed .nav-item {
  justify-content: center;
}

.task-indicator {
  position: absolute;
  top: 6px;
  right: 10px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.85);
  box-shadow: 0 0 0 2px rgba(15, 23, 42, 0.8);
}

.task-indicator.running {
  border: 1px solid rgba(56, 189, 248, 0.8);
}

.task-indicator.completed {
  border: 1px solid rgba(16, 185, 129, 0.8);
}

.task-indicator.failed {
  border: 1px solid rgba(248, 113, 113, 0.8);
}

.task-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.task-indicator.completed .task-dot {
  color: #10b981;
}

.task-indicator.failed .task-dot {
  color: #f87171;
}

.task-spinner {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid rgba(56, 189, 248, 0.4);
  border-top-color: #38bdf8;
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
