<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>欢迎使用轻量化扫描平台</span>
      </div>
    </template>
    <p>前端由 Vue3 + Vite 构建，并通过 FastAPI 直接托管。</p>
    <p>常用入口：</p>
    <ul>
      <li>前端首页（当前页）</li>
      <li><a href="/docs" target="_blank" rel="noreferrer">Swagger /docs</a></li>
      <li><a href="/api/auth/status" target="_blank" rel="noreferrer">API 健康检查</a></li>
    </ul>
  </el-card>
</template>

<script setup lang="ts"></script>

<style scoped>
.card-header {
  font-weight: 600;
}

ul {
  padding-left: 16px;
}

li + li {
  margin-top: 4px;
}
</style>
