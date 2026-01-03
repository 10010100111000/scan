<template>
  <div class="page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>后台首页</span>
          <div class="links">
            <a href="/docs" target="_blank" rel="noreferrer">Swagger</a>
            <a href="/api/auth/status" target="_blank" rel="noreferrer">Auth 状态</a>
          </div>
        </div>
      </template>
      <p>认证已完成，这是占位页面。后续可在此接入扫描任务/资产管理等模块。</p>
    </el-card>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.page {
  padding: 24px;
  background: #f8fafc;
  min-height: 100vh;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.links {
  display: flex;
  gap: 12px;
}
</style>
