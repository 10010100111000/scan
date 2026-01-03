<template>
  <div class="login-hero">
    <div class="login-card table-card">
      <div class="login-header">
        <div class="logo-mark">C</div>
        <div>
          <div class="title">Combo 控制台</div>
          <div class="subtitle">轻量化扫描 · FastAPI Admin 风格登录</div>
        </div>
      </div>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" label-width="80px" @submit.prevent>
            <el-form-item label="用户名">
              <el-input v-model="loginForm.username" autocomplete="username" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="loginForm.password" type="password" autocomplete="current-password" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loadingLogin" @click="submitLogin" style="width: 100%;">登录</el-button>
            </el-form-item>
            <div class="helper-links">
              <el-button link type="info" @click="showForgot = true">忘记密码？</el-button>
            </div>
          </el-form>
        </el-tab-pane>
        <el-tab-pane v-if="firstRun" label="初始化管理员" name="register">
          <el-alert
            type="warning"
            title="首次访问：请创建首个管理员"
            :closable="false"
            show-icon
            style="margin-bottom: 10px"
          />
          <el-form :model="registerForm" label-width="80px" @submit.prevent>
            <el-form-item label="用户名">
              <el-input v-model="registerForm.username" autocomplete="username" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="registerForm.email" autocomplete="email" placeholder="可选" />
            </el-form-item>
            <el-form-item label="密码">
              <el-input v-model="registerForm.password" type="password" autocomplete="new-password" />
            </el-form-item>
            <el-form-item>
              <el-button type="success" :loading="loadingRegister" @click="submitRegister" style="width: 100%;">
                创建并登录
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>

  <el-dialog v-model="showForgot" title="忘记密码" width="420px">
    <el-form :model="forgotForm" label-width="80px" @submit.prevent>
      <el-form-item label="用户名">
        <el-input v-model="forgotForm.username" />
      </el-form-item>
      <el-form-item label="邮箱">
        <el-input v-model="forgotForm.email" placeholder="可选，便于管理员联系" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showForgot = false">取消</el-button>
      <el-button type="primary" :loading="loadingForgot" @click="submitForgot">提交</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { fetchAuthStatus, forgotPassword, login, registerAdmin } from "../api";

const emit = defineEmits(["logged-in"]);

const activeTab = ref("login");
const firstRun = ref(false);
const showForgot = ref(false);

const loginForm = reactive({
  username: "admin",
  password: "admin123",
});
const registerForm = reactive({
  username: "admin",
  email: "",
  password: "admin123",
});
const forgotForm = reactive({
  username: "",
  email: "",
});

const loadingLogin = ref(false);
const loadingRegister = ref(false);
const loadingForgot = ref(false);

const submitLogin = async () => {
  loadingLogin.value = true;
  try {
    const res = await login(loginForm.username, loginForm.password);
    localStorage.setItem("scan_token", res.access_token);
    ElMessage.success("登录成功");
    emit("logged-in", res.access_token);
  } catch (err) {
    console.error(err);
    ElMessage.error(err?.response?.data?.detail || "登录失败");
  } finally {
    loadingLogin.value = false;
  }
};

const submitRegister = async () => {
  loadingRegister.value = true;
  try {
    const res = await registerAdmin({
      username: registerForm.username,
      email: registerForm.email || undefined,
      password: registerForm.password,
    });
    ElMessage.success("管理员创建成功，已自动登录");
    // 自动登录
    const tokenRes = await login(registerForm.username, registerForm.password);
    localStorage.setItem("scan_token", tokenRes.access_token);
    emit("logged-in", tokenRes.access_token);
  } catch (err) {
    console.error(err);
    ElMessage.error(err?.response?.data?.detail || "注册失败");
  } finally {
    loadingRegister.value = false;
  }
};

const submitForgot = async () => {
  loadingForgot.value = true;
  try {
    const res = await forgotPassword({ ...forgotForm });
    ElMessage.info(res.detail || "已提交，请联系管理员");
    showForgot.value = false;
  } catch (err) {
    console.error(err);
    ElMessage.error(err?.response?.data?.detail || "提交失败");
  } finally {
    loadingForgot.value = false;
  }
};

const loadAuthStatus = async () => {
  try {
    const data = await fetchAuthStatus();
    firstRun.value = Boolean(data.first_run);
    if (firstRun.value) {
      activeTab.value = "register";
    }
  } catch (err) {
    console.error(err);
  }
};

onMounted(() => {
  loadAuthStatus();
});
</script>
