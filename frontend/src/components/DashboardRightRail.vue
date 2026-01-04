<template>
  <aside class="right-rail">
    <div class="card-glass rail-card">
      <div class="panel-header">
        <div>
          <p class="text-faint">Quick filters</p>
          <h3>Focus</h3>
        </div>
        <el-button text size="small" type="primary">More</el-button>
      </div>
      <div class="filter-tags">
        <el-tag v-for="filter in quickFilters" :key="filter" size="large" effect="plain" class="filter-tag">
          {{ filter }}
        </el-tag>
      </div>
      <el-button type="primary" plain block size="small">Save filter</el-button>
    </div>

    <div class="card-glass rail-card">
      <div class="panel-header">
        <div>
          <p class="text-faint">Queued tasks</p>
          <h3>Queue</h3>
        </div>
      </div>
      <div class="queue-list">
        <div v-for="job in queuedJobs" :key="job.name" class="queue-item">
          <div>
            <h4>{{ job.name }}</h4>
            <p class="text-faint">{{ job.scope }}</p>
          </div>
          <el-tag :type="job.state === 'Queued' ? 'warning' : 'info'" size="small">{{ job.state }}</el-tag>
        </div>
      </div>
    </div>

    <div class="card-glass rail-card">
      <div class="panel-header">
        <div>
          <p class="text-faint">Help & links</p>
          <h3>Resources</h3>
        </div>
      </div>
      <ul class="links">
        <li v-for="link in helpfulLinks" :key="link.label">
          <el-icon><Link /></el-icon>
          <div>
            <p>{{ link.label }}</p>
            <span class="text-faint">{{ link.desc }}</span>
          </div>
        </li>
      </ul>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { Link } from '@element-plus/icons-vue'

const quickFilters = ['High risk', 'New assets', 'Needs review', 'Today', 'External exposure']

const queuedJobs = [
  { name: 'Nightly full scan', scope: '120 targets · 5 nodes', state: 'Queued' },
  { name: 'Directory brute-force', scope: 'api.cloud.example', state: 'Preparing' },
  { name: 'Compliance checks', scope: 'Production assets', state: 'Queued' },
]

const helpfulLinks = [
  { label: 'Connect real data', desc: 'Read the API guide and samples' },
  { label: 'Risk handling', desc: 'Default priorities and scoring' },
  { label: 'Feedback & requests', desc: 'Share needs with the team' },
]
</script>

<style scoped>
.right-rail {
  position: sticky;
  top: 16px;
  align-self: start;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
  box-sizing: border-box;
}

.rail-card {
  padding: 16px;
  border-radius: 16px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.panel-header h3 {
  margin: 4px 0 0;
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.filter-tag {
  padding: 8px 12px;
}

.queue-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.queue-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.links {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.links li {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 10px;
  padding: 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  align-items: center;
}

.links p {
  margin: 0;
}
</style>
