<template>
  <div class="login-hero">
    <div class="login-card table-card">
      <div class="login-header">
        <div class="logo-mark">C</div>
        <div>
          <div class="title">Combo 控制台</div>
          <div class="subtitle">Vben Admin 风格 · 暗色界面</div>
        </div>
      </div>
      <a-tabs v-model:activeKey="activeTab">
        <a-tab-pane key="login" tab="登录">
          <a-form layout="vertical">
            <a-form-item label="用户名">
              <a-input v-model:value="loginForm.username" autocomplete="username" />
            </a-form-item>
            <a-form-item label="密码">
              <a-input-password v-model:value="loginForm.password" autocomplete="current-password" />
            </a-form-item>
            <a-button type="primary" block :loading="loadingLogin" @click="submitLogin">登录</a-button>
            <div class="helper-links">
              <a-button type="link" @click="showForgot = true">忘记密码？</a-button>
            </div>
          </a-form>
        </a-tab-pane>
        <a-tab-pane v-if="firstRun" key="register" tab="初始化管理员">
          <a-alert
            type="warning"
            message="首次访问：请创建首个管理员"
            banner
            style="margin-bottom: 10px"
          />
          <a-form layout="vertical">
            <a-form-item label="用户名">
              <a-input v-model:value="registerForm.username" autocomplete="username" />
            </a-form-item>
            <a-form-item label="邮箱">
              <a-input v-model:value="registerForm.email" autocomplete="email" placeholder="可选" />
            </a-form-item>
            <a-form-item label="密码">
              <a-input-password v-model:value="registerForm.password" autocomplete="new-password" />
            </a-form-item>
            <a-button type="primary" block :loading="loadingRegister" @click="submitRegister">
              创建并登录
            </a-button>
          </a-form>
        </a-tab-pane>
      </a-tabs>
    </div>
  </div>

  <a-modal v-model:open="showForgot" title="忘记密码" ok-text="提交" cancel-text="取消" :confirm-loading="loadingForgot" @ok="submitForgot">
    <a-form layout="vertical">
      <a-form-item label="用户名">
        <a-input v-model:value="forgotForm.username" />
      </a-form-item>
      <a-form-item label="邮箱">
        <a-input v-model:value="forgotForm.email" placeholder="可选，便于管理员联系" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { message, Modal } from "ant-design-vue";
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
    message.success("登录成功");
    emit("logged-in", res.access_token);
  } catch (err) {
    console.error(err);
    message.error(err?.response?.data?.detail || "登录失败");
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
    message.success("管理员创建成功，已自动登录");
    // 自动登录
    const tokenRes = await login(registerForm.username, registerForm.password);
    localStorage.setItem("scan_token", tokenRes.access_token);
    emit("logged-in", tokenRes.access_token);
  } catch (err) {
    console.error(err);
    message.error(err?.response?.data?.detail || "注册失败");
  } finally {
    loadingRegister.value = false;
  }
};

const submitForgot = async () => {
  loadingForgot.value = true;
  try {
    const res = await forgotPassword({ ...forgotForm });
    message.info(res.detail || "已提交，请联系管理员");
    showForgot.value = false;
  } catch (err) {
    console.error(err);
    message.error(err?.response?.data?.detail || "提交失败");
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
