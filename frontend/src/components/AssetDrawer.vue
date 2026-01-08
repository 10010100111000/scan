<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" @click="close" class="fixed inset-0 bg-black/20 z-40" />
    </Transition>

    <Transition name="slide">
      <aside v-if="visible" class="fixed top-0 right-0 bottom-0 w-[500px] max-w-[90vw] bg-[#0f172a]/95 backdrop-blur-xl border-l border-white/10 shadow-2xl z-50 flex flex-col text-slate-300 font-sans">
        
        <div class="h-16 border-b border-white/5 flex items-center justify-between px-6 shrink-0 bg-white/5">
          <div class="flex items-center gap-3">
            <div class="w-2 h-2 rounded-full" :class="getStatusColor(asset.status, 'bg')"></div>
            <h3 class="font-bold text-slate-100 truncate max-w-[300px]" :title="asset.url">{{ asset.url }}</h3>
          </div>
          <button @click="close" class="p-2 hover:bg-white/10 rounded-lg transition-colors text-slate-400 hover:text-white">
            <el-icon size="20"><Close /></el-icon>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8">
          
          <div class="space-y-3">
            <h4 class="text-xs font-bold text-slate-500 uppercase tracking-widest">Preview</h4>
            <div class="aspect-video bg-slate-900/50 rounded-lg border border-white/10 flex items-center justify-center overflow-hidden relative group">
              <el-icon size="40" class="text-slate-700"><Picture /></el-icon>
              
              <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                 <el-button type="primary" link icon="FullScreen">View Fullscreen</el-button>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="p-4 rounded-lg bg-white/5 border border-white/5">
              <div class="text-[10px] text-slate-500 uppercase mb-1">Status Code</div>
              <div class="text-2xl font-mono font-bold" :class="getStatusColor(asset.status, 'text')">
                {{ asset.status || '---' }}
              </div>
            </div>
            <div class="p-4 rounded-lg bg-white/5 border border-white/5">
              <div class="text-[10px] text-slate-500 uppercase mb-1">Web Server</div>
              <div class="text-2xl font-mono text-slate-300 truncate" title="nginx/1.18.0">
                {{ getTechVersion(asset.tech, 'Nginx') || 'Unknown' }}
              </div>
            </div>
          </div>

          <div class="space-y-3">
            <h4 class="text-xs font-bold text-slate-500 uppercase tracking-widest">Technologies</h4>
            <div class="flex flex-wrap gap-2">
              <div v-for="(ver, name) in asset.tech || {}" :key="name"
                   class="flex items-center gap-3 px-3 py-2 rounded border border-white/10 bg-white/5 hover:border-blue-500/50 transition-colors cursor-default select-none">
                <div class="w-1.5 h-1.5 rounded-full bg-blue-400"></div>
                <span class="text-sm text-slate-200 font-medium">{{ name }}</span>
                <span v-if="ver" class="ml-2 text-xs text-slate-500 font-mono">{{ ver }}</span>
              </div>
              <div v-if="!asset.tech" class="text-slate-600 text-sm italic">No technologies detected.</div>
            </div>
          </div>

          <div class="space-y-3">
            <h4 class="text-xs font-bold text-slate-500 uppercase tracking-widest">Response Headers</h4>
            <div class="bg-slate-950/50 rounded-lg border border-white/10 p-4 overflow-x-auto relative group">
              <pre class="font-mono text-xs text-slate-400 leading-relaxed">
HTTP/1.1 {{ asset.status }} OK
Date: {{ new Date().toUTCString() }}
Content-Type: text/html; charset=utf-8
Connection: keep-alive
Server: {{ getTechVersion(asset.tech, 'Server') || 'gunicorn' }}
X-Powered-By: React
Content-Length: 1024</pre>
              <button class="absolute top-2 right-2 p-1.5 rounded bg-white/10 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity hover:text-white">
                 <el-icon><CopyDocument /></el-icon>
              </button>
            </div>
          </div>

        </div>
        
        <div class="p-4 border-t border-white/5 bg-slate-900/50 flex gap-3">
           <el-button type="primary" class="flex-1" @click="openLink(asset.url)">
             <el-icon class="mr-2"><Link /></el-icon> Visit Site
           </el-button>
           <el-button plain type="danger" icon="Delete" />
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Close, Picture, Link, CopyDocument, FullScreen, Delete } from '@element-plus/icons-vue'

const props = defineProps<{
  visible: boolean
  asset: any
}>()

const emit = defineEmits(['close'])

const close = () => emit('close')

const openLink = (url: string) => window.open(url, '_blank')

const getStatusColor = (code: number, type: 'bg' | 'text') => {
  if (!code) return type === 'bg' ? 'bg-slate-700' : 'text-slate-500'
  if (code >= 200 && code < 300) return type === 'bg' ? 'bg-emerald-500' : 'text-emerald-400'
  if (code >= 300 && code < 400) return type === 'bg' ? 'bg-blue-500' : 'text-blue-400'
  if (code >= 400 && code < 500) return type === 'bg' ? 'bg-orange-500' : 'text-orange-400'
  return type === 'bg' ? 'bg-red-500' : 'text-red-400'
}

// 辅助函数：尝试从 tech 对象中获取特定名称的版本（模拟）
const getTechVersion = (tech: any, key: string) => {
  if (!tech) return ''
  // 简单的模糊匹配演示
  const k = Object.keys(tech).find(k => k.toLowerCase().includes(key.toLowerCase()))
  return k ? tech[k] : ''
}
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 独立滚动条样式，防止影响全局 */
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 3px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }
</style>