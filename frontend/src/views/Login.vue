<template>
  <div class="auth-layout">
    <el-card class="auth-card">
      <template #header>
        <div class="card-header">
          <span>登录</span>
          <a href="/docs" target="_blank" rel="noreferrer">API 文档</a>
        </div>
      </template>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px" @keyup.enter="onSubmit">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" autocomplete="current-password" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="onSubmit">Login</el-button>
          <el-button link type="primary" @click="goReset">Reset Password</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, FormInstance, FormRules } from "element-plus";
import { useAuthStore } from "@/stores/auth";

const auth = useAuthStore();
const router = useRouter();

const formRef = ref<FormInstance>();
const form = reactive({
  username: "",
  password: "",
});

const rules: FormRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

const loading = ref(false);

const onSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    loading.value = true;
    try {
      await auth.login({ username: form.username, password: form.password });
      ElMessage.success("登录成功");
      router.push("/app");
    } catch (error: any) {
      const msg = error?.response?.data?.message || error?.message || "登录失败";
      ElMessage.error(msg);
    } finally {
      loading.value = false;
    }
  });
};

const goReset = () => {
  router.push("/reset-password");
};
</script>

<style scoped>
.auth-layout {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f8fafc;
}

.auth-card {
  width: 420px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
