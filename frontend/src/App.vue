<template>
  <div class="layout">
    <header class="app-header">
      <div class="brand">Scan Console</div>
      <nav class="nav-links">
        <RouterLink to="/">首页</RouterLink>
        <RouterLink to="/login">登录</RouterLink>
        <a href="/docs" target="_blank" rel="noreferrer">API 文档</a>
      </nav>
    </header>

    <main class="app-main">
      <RouterView />
    </main>

    <footer class="app-footer">
      <small>轻量化资产扫描平台 · 前后端一体化部署</small>
    </footer>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: #0f172a;
  color: #e2e8f0;
}

.brand {
  font-weight: 700;
  letter-spacing: 0.5px;
}

.nav-links {
  display: flex;
  gap: 16px;
}

.nav-links a {
  color: #cbd5e1;
  text-decoration: none;
  font-weight: 500;
}

.nav-links a.router-link-active {
  color: #ffffff;
  text-decoration: underline;
}

.app-main {
  flex: 1;
  padding: 24px;
  background: #f8fafc;
}

.app-footer {
  padding: 12px 24px;
  text-align: center;
  background: #0f172a;
  color: #cbd5e1;
}
</style>
