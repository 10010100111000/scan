<template>
  <div class="auth-layout">
    <div class="panel">
      <div class="brand">
        <div class="logo">🔐</div>
        <div class="title">
          <h2>Scan Console</h2>
          <p>登录后台</p>
        </div>
      </div>

      <el-form :model="form" :rules="rules" ref="formRef" label-position="top" @keyup.enter="onSubmit">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" size="large" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" size="large" type="password" autocomplete="current-password" />
        </el-form-item>
        <div class="actions">
          <el-button type="primary" size="large" :loading="loading" class="full" @click="onSubmit">登录</el-button>
          <el-button link type="primary" @click="goReset">重置密码</el-button>
        </div>
      </el-form>
    </div>
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
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at 20% 20%, #f1f5f9 0, #e2e8f0 30%, #f8fafc 60%);
}

.panel {
  width: 440px;
  padding: 32px;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 10px 40px rgba(15, 23, 42, 0.08);
}

.brand {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 20px;
}

.logo {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #2563eb, #22c55e);
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 20px;
  box-shadow: 0 8px 20px rgba(34, 197, 94, 0.25);
}

.title h2 {
  margin: 0;
  font-weight: 700;
  color: #0f172a;
}

.title p {
  margin: 4px 0 0;
  color: #475569;
  font-size: 13px;
}

.actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 4px;
}

.full {
  width: 100%;
}
</style>
