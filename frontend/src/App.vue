<template>
  <div class="app-shell">
    <router-view />
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: radial-gradient(circle at 20% 20%, rgba(64, 158, 255, 0.08), transparent 35%),
    radial-gradient(circle at 80% 0%, rgba(103, 194, 58, 0.08), transparent 35%),
    #0f172a;
}
</style>
