<template>
  <div class="dashboard">
    <header class="dashboard__header card-glass">
      <div>
        <p class="text-faint">欢迎回来</p>
        <h2 class="hero-title">临时控制台</h2>
      </div>
      <div class="user-area">
        <el-avatar :size="40" :src="userInfo?.avatar">
          {{ userInfo?.username?.slice(0, 1).toUpperCase() }}
        </el-avatar>
        <div class="user-meta">
          <strong>{{ userInfo?.realName }}</strong>
          <span class="text-faint">{{ userInfo?.roles?.join(', ') }}</span>
        </div>
        <el-button size="small" type="danger" @click="handleLogout">退出</el-button>
      </div>
    </header>

    <main class="dashboard__content">
      <section class="card-glass placeholder">
        <h3>控制台占位</h3>
        <p class="text-faint">登录验证已打通，后续可在此嵌入资产、任务等管理界面。</p>
        <el-button type="primary" @click="refreshUser">刷新用户信息</el-button>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const userInfo = computed(() => auth.userInfo)

const refreshUser = async () => {
  await auth.fetchUserInfo()
}

const handleLogout = async () => {
  await auth.logout()
  router.replace({ name: 'Login' })
}

onMounted(async () => {
  if (!auth.userInfo && auth.token) {
    await auth.fetchUserInfo()
  }
})
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  padding: 24px;
  color: #e2e8f0;
}

.dashboard__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-radius: 16px;
  margin-bottom: 24px;
}

.user-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-meta {
  display: flex;
  flex-direction: column;
  min-width: 120px;
}

.dashboard__content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.placeholder {
  padding: 20px;
  border-radius: 16px;
}
</style>
