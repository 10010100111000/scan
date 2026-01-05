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
      <transition
        name="scan-overlay"
        @before-enter="onOverlayBeforeEnter"
        @after-enter="onOverlayAfterEnter"
        @after-leave="onOverlayAfterLeave"
      >
        <div v-if="scanOverlayOpen" class="scan-overlay" @click.self="closeScan">
          <div class="scan-overlay__backdrop" @click="closeScan"></div>
          <div class="scan-overlay__panel" @click.stop>
            <button class="scan-overlay__close" type="button" @click="closeScan" aria-label="Close scan overlay">
              <span aria-hidden="true">&times;</span>
            </button>
            <div v-if="!scanOverlayReady" class="scan-overlay__skeleton">
              <div class="skeleton-block title"></div>
              <div class="skeleton-block"></div>
              <div class="skeleton-block"></div>
              <div class="skeleton-grid">
                <div class="skeleton-block"></div>
                <div class="skeleton-block"></div>
                <div class="skeleton-block"></div>
              </div>
            </div>
            <ScanView v-else />
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
const scanOverlayReady = ref(false)

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
  if (!scanOverlayOpen.value) {
    return
  }
  if (event.key === 'Escape') {
    closeScan()
  }
}

const onOverlayBeforeEnter = () => {
  scanOverlayReady.value = false
}

const onOverlayAfterEnter = () => {
  scanOverlayReady.value = true
}

const onOverlayAfterLeave = () => {
  scanOverlayReady.value = false
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

.app-shell__grid > * {
  min-width: 0;
  box-sizing: border-box;
}

.app-shell__main {
  min-width: 0;
  width: 100%;
  display: block;
}

.app-shell__main > * {
  width: 100%;
  min-width: 0;
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
  overflow: auto;
}

.scan-overlay__close {
  position: fixed;
  top: 18px;
  right: 18px;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: rgba(15, 23, 42, 0.8);
  color: #e2e8f0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 2101;
  transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.scan-overlay__close:hover {
  transform: translateY(-1px);
  border-color: rgba(226, 232, 240, 0.5);
  background: rgba(30, 41, 59, 0.9);
}

.scan-overlay__skeleton {
  padding: 32px 48px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skeleton-block {
  height: 16px;
  border-radius: 10px;
  background: linear-gradient(90deg, rgba(148, 163, 184, 0.12), rgba(148, 163, 184, 0.28), rgba(148, 163, 184, 0.12));
  animation: shimmer 1.6s infinite;
}

.skeleton-block.title {
  height: 28px;
  width: 240px;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.scan-overlay-enter-active,
.scan-overlay-leave-active {
  transition: opacity 0.2s ease;
}

.scan-overlay-enter-from,
.scan-overlay-leave-to {
  opacity: 0;
}

.scan-overlay-enter-active .scan-overlay__panel,
.scan-overlay-leave-active .scan-overlay__panel {
  transition: transform 0.35s ease;
}

.scan-overlay-enter-from .scan-overlay__panel,
.scan-overlay-leave-to .scan-overlay__panel {
  transform: translateY(100%);
}

@keyframes shimmer {
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: 200px 0;
  }
}
</style>
