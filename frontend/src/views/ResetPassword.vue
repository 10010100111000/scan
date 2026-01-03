<template>
  <div class="auth-layout">
    <el-card class="auth-card">
      <template #header>
        <div class="card-header">
          <span>重置密码</span>
        </div>
      </template>
      <el-form :model="form" label-width="110px">
        <el-form-item label="邮箱 (可选)">
          <el-input v-model="form.email" placeholder="email@example.com" />
        </el-form-item>
        <el-form-item label="用户名 (可选)">
          <el-input v-model="form.username" placeholder="admin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="submit">提交</el-button>
          <el-button @click="goLogin">返回登录</el-button>
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon>
        当前为占位功能：后端支持 /api/auth/forgot，会返回提示信息。
      </el-alert>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import http from "@/api/http";

const router = useRouter();

const form = reactive({
  email: "",
  username: "",
});

const loading = ref(false);

const submit = async () => {
  loading.value = true;
  try {
    await http.post("/api/auth/forgot", {
      email: form.email || null,
      username: form.username || null,
    });
    ElMessage.success("已提交请求，如有需要请联系管理员。");
  } catch (error: any) {
    const msg = error?.response?.data?.message || error?.message || "提交失败";
    ElMessage.error(msg);
  } finally {
    loading.value = false;
  }
};

const goLogin = () => {
  router.push("/login");
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
  width: 480px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
