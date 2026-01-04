<template>
  <div class="auth-layout">
    <div class="panel card-glass">
      <div class="panel__header">
        <h1 class="hero-title">初始化超级管理员</h1>
        <p class="text-faint">首次运行需要创建超级管理员账号</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="panel__form">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" size="large" clearable />
        </el-form-item>

        <el-form-item label="邮箱 (可选)" prop="email">
          <el-input v-model="form.email" placeholder="admin@example.com" size="large" clearable />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" size="large" />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="form.confirm" type="password" show-password placeholder="再次输入密码" size="large" />
        </el-form-item>

        <el-button type="primary" size="large" class="panel__action" :loading="submitting" @click="handleSubmit">
          创建管理员
        </el-button>

        <div class="text-faint back-login" @click="toLogin">已有账号？前往登录</div>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirm: '',
})

const rules: FormRules<typeof form> = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirm: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

const formRef = ref<FormInstance>()
const submitting = ref(false)

const handleSubmit = () => {
  formRef.value?.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await auth.setup({
        username: form.username,
        email: form.email,
        password: form.password,
      })
      router.push({ name: 'Login' })
    } catch (error) {
      ElMessage.error((error as Error).message || '创建管理员失败')
    } finally {
      submitting.value = false
    }
  })
}

const toLogin = () => router.push({ name: 'Login' })
</script>

<style scoped>
.auth-layout {
  display: grid;
  place-items: center;
  min-height: 100vh;
  padding: 32px 16px;
}

.panel {
  width: min(520px, 96vw);
  padding: 32px;
  border-radius: 16px;
  color: #e2e8f0;
}

.panel__header {
  margin-bottom: 12px;
}

.panel__form {
  margin-top: 16px;
}

.panel__action {
  width: 100%;
  margin-top: 4px;
}

.back-login {
  margin-top: 12px;
  text-align: center;
  cursor: pointer;
}
</style>
