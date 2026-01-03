<template>
  <el-form :model="form" label-width="80px" @submit.prevent="submit">
    <el-form-item label="用户名">
      <el-input v-model="form.username" autocomplete="username" />
    </el-form-item>
    <el-form-item label="密码">
      <el-input v-model="form.password" type="password" autocomplete="current-password" />
    </el-form-item>
    <el-form-item>
      <el-button type="primary" :loading="loading" @click="submit">登录</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { login } from "../api";

const emit = defineEmits(["logged-in"]);
const form = reactive({
  username: "admin",
  password: "admin123",
});
const loading = ref(false);

const submit = async () => {
  loading.value = true;
  try {
    const res = await login(form.username, form.password);
    localStorage.setItem("scan_token", res.access_token);
    ElMessage.success("登录成功");
    emit("logged-in", res.access_token);
  } catch (err) {
    console.error(err);
    ElMessage.error(err?.response?.data?.detail || "登录失败");
  } finally {
    loading.value = false;
  }
};
</script>
