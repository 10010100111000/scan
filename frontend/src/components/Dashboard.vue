<template>
  <div class="section-grid">
    <div class="panel table-card">
      <div class="panel-header">
        <div class="panel-title">快速发起扫描</div>
        <el-tag type="info" effect="dark">自动轮询 + 实时渲染</el-tag>
      </div>
      <div class="panel-body">
        <el-form :model="form" label-width="120px" label-position="left" @submit.prevent>
          <el-form-item label="组织 ID">
            <el-input v-model="form.orgId" placeholder="已有组织 ID" />
          </el-form-item>
          <el-form-item label="资产名称">
            <el-input v-model="form.assetName" placeholder="example.com / 1.1.1.0/24" />
          </el-form-item>
          <el-form-item label="资产类型">
            <el-select v-model="form.assetType" placeholder="选择类型">
              <el-option label="域名" value="domain" />
              <el-option label="CIDR" value="cidr" />
            </el-select>
          </el-form-item>
          <el-form-item label="扫描配置">
            <el-select v-model="form.config" filterable :loading="loadingConfigs" placeholder="选择扫描器">
              <el-option v-for="c in scanConfigs" :key="c.name" :label="c.name" :value="c.name">
                <span>{{ c.name }}</span>
                <span style="color: #94a3b8; margin-left: 8px;">({{ c.agent_type || "unknown" }})</span>
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="launching" @click="launchScan">创建资产并扫描</el-button>
          </el-form-item>
        </el-form>

        <el-divider />
        <div class="panel-title" style="margin-bottom: 12px;">任务日志</div>
        <div class="log-area" style="height: 220px;">
          <el-scrollbar ref="logScrollbar" height="200px">
            <div v-if="logLines.length === 0" style="color: #64748b;">等待任务...</div>
            <div v-for="(line, idx) in logLines" :key="idx">{{ line }}</div>
          </el-scrollbar>
        </div>
        <div style="margin-top: 10px; display: flex; gap: 8px; align-items: center;">
          <el-tag :type="statusTag.type" effect="dark">{{ statusTag.text }}</el-tag>
          <span v-if="currentTaskId" style="color: #94a3b8;">任务 ID: {{ currentTaskId }}</span>
        </div>
      </div>
    </div>

    <div class="panel table-card">
      <div class="panel-header">
        <div class="panel-title">最近任务</div>
        <el-button size="small" @click="loadTasks">刷新</el-button>
      </div>
      <div class="panel-body">
        <el-table :data="tasks" border size="small" height="360">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="config_name" label="配置" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusToTag(row.status)">{{ row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="160" />
        </el-table>
      </div>
    </div>
  </div>

  <div class="panel" style="margin-top: 16px;">
    <div class="panel-header">
      <div class="panel-title">最新结果</div>
      <div style="color: #94a3b8;">完成后自动拉取子域 / 端口 / Web / 漏洞</div>
    </div>
    <div class="panel-body">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="子域名" name="hosts">
          <el-table :data="hosts" size="small" border height="260">
            <el-table-column prop="hostname" label="Host" />
            <el-table-column prop="status" label="状态" width="120" />
            <el-table-column prop="ips" label="IP" />
            <el-table-column prop="created_at" label="发现时间" width="180" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="端口" name="ports">
          <el-table :data="ports" size="small" border height="260">
            <el-table-column prop="ip" label="IP" />
            <el-table-column prop="port" label="端口" width="100" />
            <el-table-column prop="service" label="服务" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="Web" name="web">
          <el-table :data="web" size="small" border height="260">
            <el-table-column prop="url" label="URL" />
            <el-table-column prop="status" label="状态码" width="100" />
            <el-table-column prop="title" label="标题" />
            <el-table-column prop="tech" label="技术栈" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="漏洞" name="vulns">
          <el-table :data="vulns" size="small" border height="260">
            <el-table-column prop="name" label="名称" />
            <el-table-column prop="severity" label="严重性" width="120">
              <template #default="{ row }">
                <el-tag :type="severityTag(row.severity)">{{ row.severity }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="url" label="命中 URL" />
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import {
  createAsset,
  fetchHosts,
  fetchPorts,
  fetchScanConfigs,
  fetchVulns,
  fetchWeb,
  getTask,
  listTasks,
  triggerScan,
} from "../api";

const props = defineProps({
  token: String,
});

const form = reactive({
  orgId: "",
  assetName: "",
  assetType: "domain",
  config: "",
});

const logLines = ref([]);
const currentTaskId = ref(null);
const currentAssetId = ref(null);
const pollingTimer = ref(null);
const launching = ref(false);
const loadingConfigs = ref(false);
const scanConfigs = ref([]);
const tasks = ref([]);
const activeTab = ref("hosts");

const hosts = ref([]);
const ports = ref([]);
const web = ref([]);
const vulns = ref([]);
const logScrollbar = ref(null);

const statusTag = computed(() => {
  if (!currentTaskId.value) return { text: "待启动", type: "info" };
  if (logLines.value.find((l) => l.includes("failed"))) return { text: "失败", type: "danger" };
  return { text: "运行中", type: "success" };
});

const statusToTag = (status) => {
  const map = {
    pending: "info",
    running: "warning",
    completed: "success",
    failed: "danger",
  };
  return map[status] || "info";
};

const severityTag = (sev) => {
  const map = {
    critical: "danger",
    high: "danger",
    medium: "warning",
    low: "info",
    info: "info",
  };
  return map[sev] || "info";
};

const loadConfigs = async () => {
  loadingConfigs.value = true;
  try {
    const data = await fetchScanConfigs();
    scanConfigs.value = data;
    if (!form.config && data.length) form.config = data[0].name;
  } catch (err) {
    console.error(err);
    ElMessage.error("无法加载扫描配置");
  } finally {
    loadingConfigs.value = false;
  }
};

const loadTasks = async () => {
  try {
    tasks.value = await listTasks({ limit: 20 });
  } catch (err) {
    console.error(err);
    ElMessage.error("获取任务列表失败");
  }
};

const appendLog = (line) => {
  logLines.value.push(line);
  requestAnimationFrame(() => {
    logScrollbar.value?.setScrollTop(99999);
  });
};

const pollTask = async () => {
  if (!currentTaskId.value) return;
  try {
    const task = await getTask(currentTaskId.value);
    appendLog(`[${task.status}] ${task.log || "执行中..."}`);
    if (task.status === "completed" || task.status === "failed") {
      clearInterval(pollingTimer.value);
      pollingTimer.value = null;
      await loadResults();
      await loadTasks();
    }
  } catch (err) {
    console.error(err);
    appendLog("查询任务失败");
  }
};

const loadResults = async () => {
  if (!currentAssetId.value) return;
  try {
    const [hostData, portData, webData, vulnData] = await Promise.all([
      fetchHosts(currentAssetId.value),
      fetchPorts(currentAssetId.value),
      fetchWeb(currentAssetId.value),
      fetchVulns(currentAssetId.value),
    ]);
    hosts.value = hostData;
    ports.value = portData;
    web.value = webData;
    vulns.value = vulnData;
    ElMessage.success("结果已更新");
  } catch (err) {
    console.error(err);
    ElMessage.error("获取结果失败");
  }
};

const launchScan = async () => {
  if (!form.orgId || !form.assetName || !form.config) {
    ElMessage.warning("请完整填写组织、资产与扫描配置");
    return;
  }
  launching.value = true;
  logLines.value = [];
  try {
    const asset = await createAsset(form.orgId, { name: form.assetName, type: form.assetType });
    currentAssetId.value = asset.id;
    appendLog(`资产创建成功 #${asset.id}`);
    const task = await triggerScan(asset.id, form.config);
    currentTaskId.value = task.id;
    appendLog(`任务下发成功 #${task.id} (${task.config_name})`);
    if (pollingTimer.value) clearInterval(pollingTimer.value);
    pollingTimer.value = setInterval(pollTask, 3000);
  } catch (err) {
    console.error(err);
    ElMessage.error(err?.response?.data?.detail || "发起任务失败");
  } finally {
    launching.value = false;
  }
};

watch(
  () => props.token,
  () => {
    loadTasks();
    loadConfigs();
  },
  { immediate: true }
);

onMounted(() => {
  loadConfigs();
  loadTasks();
});

onBeforeUnmount(() => {
  if (pollingTimer.value) clearInterval(pollingTimer.value);
});
</script>
