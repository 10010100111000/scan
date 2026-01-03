<template>
  <div class="app-shell">
    <div class="panel" style="max-width: 1080px; margin: 0 auto 20px auto;">
      <div class="panel-header">
        <div class="panel-title">Combo 扫描控制台</div>
        <div v-if="token" class="pill">已登录</div>
      </div>
      <div class="panel-body">
        <LoginView v-if="!token" @logged-in="onLogin" />
        <Dashboard v-else :token="token" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import LoginView from "./components/LoginView.vue";
import Dashboard from "./components/Dashboard.vue";

const token = ref(localStorage.getItem("scan_token"));

const onLogin = (newToken) => {
  token.value = newToken;
};
</script>
