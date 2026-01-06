<template>
  <div class="app-shell">
    <div class="app-shell__grid" :style="gridStyle">
      <NavRail :collapsed="railCollapsed" @toggle="toggleRail" />

      <main class="app-shell__main">
        <router-view />
      </main>

      <DashboardRightRail v-if="showRightRail" class="app-shell__right" />
    </div>

    <Teleport to="body">
      <transition name="scan-overlay">
        <div v-if="scanOverlayOpen" class="scan-overlay" @click.self="closeScan">
          <div class="scan-overlay__backdrop" @click="closeScan"></div>
          <div class="scan-overlay__panel" @click.stop>
            <button class="scan-overlay__close" type="button" @click="closeScan" aria-label="Close scan overlay">
              <span aria-hidden="true">&times;</span>
            </button>
            
            <ScanView />
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import DashboardRightRail from '@/components/DashboardRightRail.vue'
import NavRail from '@/components/NavRail.vue'
import ScanView from '@/views/ScanView.vue'
import { provideScanOverlay } from '@/composables/useScanOverlay'

const route = useRoute()
const railCollapsed = ref(false)
const scanOverlayOpen = ref(false)
// 移除 scanOverlayReady 相关逻辑，不再需要延迟显示

const showRightRail = computed(() => route.meta.showRightRail === true)
const gridStyle = computed(() => ({
  '--rail-width': railCollapsed.value ? '84px' : '260px',
  '--right-width': showRightRail.value ? '320px' : '0px',
  '--main-min': '720px',
}))

const toggleRail = () => {
  railCollapsed.value = !railCollapsed.value
}

const openScan = () => {
  scanOverlayOpen.value = true
}

const closeScan = () => {
  scanOverlayOpen.value = false
}

const handleKeydown = (event: KeyboardEvent) => {
  if (!scanOverlayOpen.value) return
  if (event.key === 'Escape') closeScan()
}

provideScanOverlay({
  open: openScan,
  close: closeScan,
  toggle: () => {
    scanOverlayOpen.value ? closeScan() : openScan()
  },
})

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.body.classList.remove('scan-overlay-open')
})

watch(scanOverlayOpen, (isOpen) => {
  document.body.classList.toggle('scan-overlay-open', isOpen)
})
</script>

<style scoped>
.app-shell {
  min-height: 100vh;
  overflow-x: auto;
  background: radial-gradient(circle at 15% 20%, rgba(56, 189, 248, 0.08), transparent 35%),
    radial-gradient(circle at 80% 10%, rgba(99, 102, 241, 0.08), transparent 35%),
    #0b1020;
}

.app-shell__grid {
  display: grid;
  grid-template-columns: var(--rail-width) minmax(var(--main-min), 1fr) var(--right-width);
  gap: 12px;
  padding: 24px;
  min-height: 100vh;
  min-width: calc(var(--rail-width) + var(--main-min) + var(--right-width));
  transition: grid-template-columns 0.2s ease;
  box-sizing: border-box;
}

.app-shell__main {
  min-width: 0;
  width: 100%;
}

.app-shell__right {
  min-width: 0;
  width: 100%;
}

:global(body.scan-overlay-open) {
  overflow: hidden;
}

.scan-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: grid;
  /* 确保整个 Overlay 不会滚动 */
  overflow: hidden; 
}

.scan-overlay__backdrop {
  position: absolute;
  inset: 0;
  background: rgba(2, 6, 23, 0.72);
  backdrop-filter: blur(2px);
}

.scan-overlay__panel {
  position: relative;
  margin-top: auto;
  height: 100%;
  width: 100%;
  background: #0b1020;
  box-shadow: 0 -24px 80px rgba(0, 0, 0, 0.4);
  /* 关键修改：禁止 Panel 出现滚动条，交由 ScanView 内部处理布局 */
  overflow: hidden; 
}

.scan-overlay__close {
  position: fixed;
  top: 24px;
  right: 24px;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.1);
  background: rgba(15, 23, 42, 0.6);
  color: #94a3b8;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 2101;
  backdrop-filter: blur(4px);
  transition: all 0.2s ease;
}

.scan-overlay__close:hover {
  background: rgba(30, 41, 59, 0.8);
  color: #fff;
  border-color: rgba(148, 163, 184, 0.3);
}

.scan-overlay-enter-active,
.scan-overlay-leave-active {
  transition: opacity 0.3s ease;
}

.scan-overlay-enter-from,
.scan-overlay-leave-to {
  opacity: 0;
}

.scan-overlay-enter-active .scan-overlay__panel,
.scan-overlay-leave-active .scan-overlay__panel {
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.scan-overlay-enter-from .scan-overlay__panel,
.scan-overlay-leave-to .scan-overlay__panel {
  transform: translateY(100%);
}
</style>