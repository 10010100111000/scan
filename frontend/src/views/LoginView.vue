<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <span>登录</span>
      </template>
      <el-form :model="form" label-width="80px" @submit.prevent="onSubmit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" autocomplete="current-password" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="onSubmit">登录</el-button>
          <el-button type="default" @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { useAuthStore } from "@/stores/auth";

const form = reactive({
  username: "",
  password: "",
});

const loading = ref(false);
const authStore = useAuthStore();

const onSubmit = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning("请输入用户名和密码");
    return;
  }
  loading.value = true;
  try {
    await authStore.login({
      username: form.username,
      password: form.password,
    });
    ElMessage.success("登录成功");
  } catch (error: any) {
    const msg = error?.response?.data?.detail || error?.message || "登录失败";
    ElMessage.error(msg);
  } finally {
    loading.value = false;
  }
};

const reset = () => {
  form.username = "";
  form.password = "";
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  margin-top: 64px;
}

.login-card {
  width: 400px;
}
</style>
