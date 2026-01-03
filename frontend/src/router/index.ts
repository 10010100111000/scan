import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const LoginView = () => import("@/views/Login.vue");
const SetupAdminView = () => import("@/views/SetupAdmin.vue");
const ResetPasswordView = () => import("@/views/ResetPassword.vue");
const AppHomeView = () => import("@/views/AppHome.vue");

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "root",
    component: LoginView,
  },
  {
    path: "/login",
    name: "login",
    component: LoginView,
  },
  {
    path: "/setup",
    name: "setup",
    component: SetupAdminView,
  },
  {
    path: "/reset-password",
    name: "reset-password",
    component: ResetPasswordView,
  },
  {
    path: "/app",
    name: "app",
    component: AppHomeView,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore();

  if (auth.firstRun === null) {
    await auth.fetchStatus();
  }

  const isFirstRun = auth.firstRun === true;
  const hasToken = !!auth.token;

  // 强制初始化流程
  if (isFirstRun && to.path !== "/setup") {
    return next("/setup");
  }
  if (!isFirstRun && to.path === "/setup") {
    return next("/login");
  }

  // 根路径重定向
  if (to.path === "/") {
    return next(hasToken ? "/app" : "/login");
  }

  // 认证保护
  if (to.meta.requiresAuth && !hasToken) {
    return next("/login");
  }

  // 已登录访问登录页时跳转
  if (to.path === "/login" && hasToken) {
    return next("/app");
  }

  next();
});

export default router;
