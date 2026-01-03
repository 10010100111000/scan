<template>
  <div class="section-grid">
    <a-card class="table-card" :bordered="false" title="快速发起扫描" :extra="'自动轮询 + 实时渲染'">
      <a-form layout="vertical">
        <a-form-item label="组织 ID">
          <a-input v-model:value="form.orgId" placeholder="已有组织 ID" />
        </a-form-item>
        <a-form-item label="资产名称">
          <a-input v-model:value="form.assetName" placeholder="example.com / 1.1.1.0/24" />
        </a-form-item>
        <a-form-item label="资产类型">
          <a-select v-model:value="form.assetType">
            <a-select-option value="domain">域名</a-select-option>
            <a-select-option value="cidr">CIDR</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="扫描配置">
          <a-select
            v-model:value="form.config"
            show-search
            :loading="loadingConfigs"
            placeholder="选择扫描器"
            option-filter-prop="label"
          >
            <a-select-option v-for="c in scanConfigs" :key="c.name" :value="c.name" :label="c.name">
              <span>{{ c.name }}</span>
              <span style="color: #94a3b8; margin-left: 8px;">({{ c.agent_type || "unknown" }})</span>
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-button type="primary" :loading="launching" block @click="launchScan">创建资产并扫描</a-button>
      </a-form>

      <a-divider />
      <div class="panel-title" style="margin-bottom: 12px;">任务日志</div>
      <div class="log-area" style="height: 220px;">
        <div v-if="logLines.length === 0" style="color: #64748b;">等待任务...</div>
        <div v-else class="log-scroll" ref="logScrollbar">
          <div v-for="(line, idx) in logLines" :key="idx">{{ line }}</div>
        </div>
      </div>
      <div style="margin-top: 10px; display: flex; gap: 8px; align-items: center;">
        <a-tag :color="statusTag.color">{{ statusTag.text }}</a-tag>
        <span v-if="currentTaskId" style="color: #94a3b8;">任务 ID: {{ currentTaskId }}</span>
      </div>
    </a-card>

    <a-card class="table-card" :bordered="false" title="最近任务">
      <template #extra>
        <a-button size="small" @click="loadTasks">刷新</a-button>
      </template>
      <a-table
        size="small"
        :data-source="tasks"
        :pagination="false"
        :scroll="{ y: 320 }"
        row-key="id"
        :columns="taskColumns"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="statusToTag(record.status)">{{ record.status }}</a-tag>
          </template>
          <template v-else-if="column.key === 'config_name'">
            {{ record.config_name }}
          </template>
          <template v-else-if="column.key === 'created_at'">
            {{ record.created_at }}
          </template>
          <template v-else-if="column.key === 'id'">
            {{ record.id }}
          </template>
        </template>
      </a-table>
    </a-card>
  </div>

  <a-card class="panel" :bordered="false" style="margin-top: 16px;">
    <template #title>最新结果</template>
    <template #extra><span style="color: #94a3b8;">完成后自动拉取子域 / 端口 / Web / 漏洞</span></template>
    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="hosts" tab="子域名">
        <a-table size="small" :data-source="hosts" :pagination="false" :scroll="{ y: 240 }" row-key="id">
          <a-table-column title="Host" dataIndex="hostname" key="hostname" />
          <a-table-column title="状态" dataIndex="status" key="status" />
          <a-table-column title="IP" dataIndex="ips" key="ips" />
          <a-table-column title="发现时间" dataIndex="created_at" key="created_at" />
        </a-table>
      </a-tab-pane>
      <a-tab-pane key="ports" tab="端口">
        <a-table size="small" :data-source="ports" :pagination="false" :scroll="{ y: 240 }" row-key="id">
          <a-table-column title="IP" dataIndex="ip" key="ip" />
          <a-table-column title="端口" dataIndex="port" key="port" />
          <a-table-column title="服务" dataIndex="service" key="service" />
        </a-table>
      </a-tab-pane>
      <a-tab-pane key="web" tab="Web">
        <a-table size="small" :data-source="web" :pagination="false" :scroll="{ y: 240 }" row-key="id">
          <a-table-column title="URL" dataIndex="url" key="url" />
          <a-table-column title="状态码" dataIndex="status" key="status" />
          <a-table-column title="标题" dataIndex="title" key="title" />
          <a-table-column title="技术栈" dataIndex="tech" key="tech" />
        </a-table>
      </a-tab-pane>
      <a-tab-pane key="vulns" tab="漏洞">
        <a-table size="small" :data-source="vulns" :pagination="false" :scroll="{ y: 240 }" row-key="id">
          <a-table-column title="名称" dataIndex="name" key="name" />
          <a-table-column title="严重性" key="severity" :customRender="({ record }) => record.severity" />
          <a-table-column title="命中 URL" dataIndex="url" key="url" />
        </a-table>
      </a-tab-pane>
    </a-tabs>
  </a-card>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { message } from "ant-design-vue";
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

const taskColumns = [
  { title: "ID", dataIndex: "id", key: "id", width: 80 },
  { title: "配置", dataIndex: "config_name", key: "config_name" },
  { title: "状态", dataIndex: "status", key: "status", width: 120 },
  { title: "创建时间", dataIndex: "created_at", key: "created_at", width: 180 },
];

const statusTag = computed(() => {
  if (!currentTaskId.value) return { text: "待启动", color: "blue" };
  if (logLines.value.find((l) => l.includes("failed"))) return { text: "失败", color: "red" };
  return { text: "运行中", color: "green" };
});

const statusToTag = (status) => {
  const map = {
    pending: "blue",
    running: "gold",
    completed: "green",
    failed: "red",
  };
  return map[status] || "blue";
};

const loadConfigs = async () => {
  loadingConfigs.value = true;
  try {
    const data = await fetchScanConfigs();
    scanConfigs.value = data;
    if (!form.config && data.length) form.config = data[0].name;
  } catch (err) {
    console.error(err);
    message.error("无法加载扫描配置");
  } finally {
    loadingConfigs.value = false;
  }
};

const loadTasks = async () => {
  try {
    tasks.value = await listTasks({ limit: 20 });
  } catch (err) {
    console.error(err);
    message.error("获取任务列表失败");
  }
};

const appendLog = (line) => {
  logLines.value.push(line);
  requestAnimationFrame(() => {
    const el = logScrollbar.value;
    if (el) el.scrollTop = el.scrollHeight;
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
    message.success("结果已更新");
  } catch (err) {
    console.error(err);
    message.error("获取结果失败");
  }
};

const launchScan = async () => {
  if (!form.orgId || !form.assetName || !form.config) {
    message.warning("请完整填写组织、资产与扫描配置");
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
    message.error(err?.response?.data?.detail || "发起任务失败");
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
