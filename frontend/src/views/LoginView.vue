<template>
  <div class="auth-layout">
    <div class="panel card-glass">
      <div class="panel__left">
        <div class="logo-circle">CA</div>
        <div>
          <p class="badge">combo admin</p>
          <h1 class="hero-title">安全扫描管理控制台</h1>
          <p class="text-faint">基于 FastAPI 的轻量后台，延续 fastapi-admin 的简洁风格。</p>
        </div>
      </div>
      <div class="panel__right">
        <p class="text-faint">请使用管理员账号登录</p>
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="panel__form">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="请输入用户名" size="large" clearable />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" size="large" />
          </el-form-item>

          <el-button type="primary" size="large" class="panel__action" :loading="submitting" @click="handleSubmit">
            登录
          </el-button>

          <div class="text-faint tips">
            没有账号？
            <el-link type="primary" :underline="false" @click.prevent="goSetup">前往初始化</el-link>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules<typeof form> = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const formRef = ref<FormInstance>()
const submitting = ref(false)

const handleSubmit = () => {
  formRef.value?.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await auth.login({ ...form })
      const redirect = (route.query.redirect as string) || '/dashboard'
      router.replace(redirect)
    } catch (error) {
      ElMessage.error((error as Error).message || '登录失败')
    } finally {
      submitting.value = false
    }
  })
}

const goSetup = () => router.push({ name: 'Setup' })

onMounted(async () => {
  if (!auth.statusChecked) {
    await auth.fetchAuthStatus()
  }
  if (auth.isAuthenticated) {
    router.replace({ name: 'Dashboard' })
    return
  }
  if (auth.firstRun) {
    router.replace({ name: 'Setup' })
  }
})
</script>

<style scoped>
.auth-layout {
  display: grid;
  place-items: center;
  min-height: 100vh;
  padding: 32px 16px;
  background: radial-gradient(circle at 20% 20%, rgba(64, 158, 255, 0.12), transparent 35%),
    radial-gradient(circle at 80% 0%, rgba(103, 194, 58, 0.12), transparent 35%),
    #0d1220;
}

.panel {
  width: min(920px, 96vw);
  padding: 32px;
  border-radius: 18px;
  color: #e2e8f0;
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 28px;
}

.panel__left {
  display: flex;
  gap: 16px;
  align-items: center;
}

.panel__right {
  border-left: 1px solid rgba(255, 255, 255, 0.06);
  padding-left: 24px;
}

.badge {
  display: inline-block;
  padding: 6px 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 12px;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.logo-circle {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-weight: 700;
  letter-spacing: 1px;
  color: #0f172a;
  background: linear-gradient(135deg, #66b1ff, #67c23a);
  box-shadow: 0 10px 30px rgba(79, 177, 255, 0.35);
}

.panel__header {
  margin-bottom: 16px;
}

.panel__form {
  margin-top: 12px;
}

.panel__action {
  width: 100%;
  margin-top: 4px;
}

.tips {
  text-align: center;
  margin-top: 10px;
}
</style>
