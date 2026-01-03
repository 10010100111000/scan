<template>
  <div class="auth-layout">
    <el-card class="auth-card">
      <template #header>
        <div class="card-header">
          <span>初始化管理员</span>
        </div>
      </template>
      <el-alert type="info" :closable="false" class="mb-3" show-icon>
        <p>检测到系统尚未初始化，请创建首个管理员账号。</p>
      </el-alert>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="110px" @keyup.enter="onSubmit">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm">
          <el-input v-model="form.confirm" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="onSubmit">初始化</el-button>
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
  confirm: "",
});

const rules: FormRules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 8, message: "密码长度至少 8 位", trigger: "blur" },
  ],
  confirm: [
    { required: true, message: "请再次输入密码", trigger: "blur" },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.password) {
          callback(new Error("两次密码不一致"));
        } else {
          callback();
        }
      },
      trigger: "blur",
    },
  ],
};

const loading = ref(false);

const onSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    loading.value = true;
    try {
      await auth.setupAdmin({ username: form.username, password: form.password });
      ElMessage.success("初始化成功，请登录");
      router.push("/login");
    } catch (error: any) {
      const msg = error?.response?.data?.message || error?.message || "初始化失败";
      ElMessage.error(msg);
    } finally {
      loading.value = false;
    }
  });
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

.mb-3 {
  margin-bottom: 12px;
}
</style>
