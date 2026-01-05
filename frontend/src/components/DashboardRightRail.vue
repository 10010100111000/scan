<template>
  <aside class="right-rail">
    <div class="card-glass rail-card">
      <div class="panel-header">
        <div>
          <p class="text-faint">快捷筛选</p>
          <h3>聚焦</h3>
        </div>
        <el-button text size="small" type="primary">更多</el-button>
      </div>
      <div class="filter-tags">
        <el-tag v-for="filter in quickFilters" :key="filter" size="large" effect="plain" class="filter-tag">
          {{ filter }}
        </el-tag>
      </div>
      <el-button type="primary" plain block size="small">保存筛选</el-button>
    </div>

    <div class="card-glass rail-card">
      <div class="panel-header">
        <div>
          <p class="text-faint">帮助与链接</p>
          <h3>资源</h3>
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

const quickFilters = ['高风险', '新增资产', '需要确认', '今天', '对外暴露']

const helpfulLinks = [
  { label: '接入真实数据', desc: '查看 API 指南与示例' },
  { label: '风险处理', desc: '默认优先级与评分规则' },
  { label: '反馈与需求', desc: '提交给产品待办池' },
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
  width: 100%;
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
