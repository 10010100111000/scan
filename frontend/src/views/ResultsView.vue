<template>
  <section class="results-view">
    <header class="results-header card-glass">
      <div>
        <p class="text-faint">Results</p>
        <h2 class="hero-title">Scan Findings</h2>
        <p class="text-faint">Filter and review discovered assets, services, and issues.</p>
      </div>
      <div class="results-actions">
        <el-input v-model="query" size="small" clearable placeholder="Search host or issue" />
        <el-select v-model="severity" size="small" placeholder="Severity">
          <el-option v-for="level in severityOptions" :key="level" :label="level" :value="level" />
        </el-select>
        <el-button size="small" type="primary">Refresh</el-button>
      </div>
    </header>

    <section class="results-grid">
      <div class="card-glass results-card">
        <div class="card-header">
          <h3>Subdomains</h3>
          <el-tag size="small" effect="plain">{{ filteredHosts.length }}</el-tag>
        </div>
        <div class="card-body">
          <div v-for="host in filteredHosts" :key="host.id" class="result-row">
            <div>
              <strong>{{ host.name }}</strong>
              <p class="text-faint">{{ host.ip }}</p>
            </div>
            <el-tag size="small" effect="plain">{{ host.status }}</el-tag>
          </div>
        </div>
      </div>

      <div class="card-glass results-card">
        <div class="card-header">
          <h3>Vulnerabilities</h3>
          <el-tag size="small" effect="plain">{{ filteredVulns.length }}</el-tag>
        </div>
        <div class="card-body">
          <div v-for="vuln in filteredVulns" :key="vuln.id" class="result-row">
            <div>
              <strong>{{ vuln.title }}</strong>
              <p class="text-faint">{{ vuln.target }}</p>
            </div>
            <el-tag size="small" :type="tagType(vuln.severity)" effect="dark">{{ vuln.severity }}</el-tag>
          </div>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

type Host = { id: number; name: string; ip: string; status: string }
type Vuln = { id: number; title: string; target: string; severity: 'Low' | 'Medium' | 'High' | 'Critical' }

const query = ref('')
const severity = ref('All')
const severityOptions = ['All', 'Low', 'Medium', 'High', 'Critical']

const hosts = ref<Host[]>([
  { id: 1, name: 'api.cloud.example', ip: '10.12.3.21', status: 'Alive' },
  { id: 2, name: 'cdn.edge.internal', ip: '172.19.4.11', status: 'Alive' },
  { id: 3, name: 'jump.dev.lab', ip: '10.8.0.5', status: 'Idle' },
])

const vulns = ref<Vuln[]>([
  { id: 1, title: 'Legacy admin panel', target: 'api.cloud.example', severity: 'High' },
  { id: 2, title: 'Outdated nginx', target: 'cdn.edge.internal', severity: 'Medium' },
  { id: 3, title: 'Weak SSH banner', target: 'jump.dev.lab', severity: 'Low' },
])

const filteredHosts = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  if (!keyword) {
    return hosts.value
  }
  return hosts.value.filter((host) => host.name.toLowerCase().includes(keyword) || host.ip.includes(keyword))
})

const filteredVulns = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  return vulns.value.filter((vuln) => {
    const matchesQuery =
      !keyword || vuln.title.toLowerCase().includes(keyword) || vuln.target.toLowerCase().includes(keyword)
    const matchesSeverity = severity.value === 'All' || vuln.severity === severity.value
    return matchesQuery && matchesSeverity
  })
})

const tagType = (level: Vuln['severity']) => {
  switch (level) {
    case 'Critical':
      return 'danger'
    case 'High':
      return 'danger'
    case 'Medium':
      return 'warning'
    default:
      return 'info'
  }
}
</script>

<style scoped>
.results-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 16px;
}

.results-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.results-card {
  padding: 16px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
}
</style>
