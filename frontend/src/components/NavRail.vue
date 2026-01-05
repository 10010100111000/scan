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
        :key="item.label"
        :to="item.route"
        :class="['nav-item', { active: isActive(item.route) }]"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span v-if="!collapsed">{{ item.label }}</span>
      </router-link>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useRoute, useRouter, type RouteLocationRaw } from 'vue-router'
import { Compass, DataBoard, Expand, Fold, Monitor, Plus, Timer, User } from '@element-plus/icons-vue'
import { useScanOverlay } from '@/composables/useScanOverlay'
import type { Component } from 'vue'

defineProps<{ collapsed: boolean }>()
defineEmits<{ (event: 'toggle'): void }>()

const route = useRoute()
const router = useRouter()
const { open: openScan } = useScanOverlay()

const navLinks: Array<{ label: string; icon: Component; route: RouteLocationRaw }> = [
  { label: '仪表盘', icon: DataBoard, route: { name: 'Dashboard' } },
  { label: '任务流', icon: Timer, route: { name: 'Tasks' } },
  { label: '资产', icon: Monitor, route: { name: 'Assets' } },
  { label: '初始化', icon: Compass, route: { name: 'Setup' } },
  { label: '账号', icon: User, route: { name: 'Login' } },
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
</style>
