import { createRouter, createWebHistory, NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      redirect: { name: 'Dashboard' },
    },
    {
      path: '/setup',
      name: 'Setup',
      component: () => import('@/views/SetupView.vue'),
      meta: { requiresFirstRun: true },
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/scan',
      name: 'Scan',
      component: () => import('@/views/ScanView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

async function authGuard(to: RouteLocationNormalized, next: NavigationGuardNext) {
  const auth = useAuthStore()
  if (!auth.statusChecked) {
    await auth.fetchAuthStatus()
  }

  if (auth.firstRun) {
    if (to.name !== 'Setup') {
      return next({ name: 'Setup' })
    }
    return next()
  }

  if (to.name === 'Setup') {
    return next({ name: 'Login' })
  }

  if (auth.token && !auth.userInfo) {
    try {
      await auth.fetchUserInfo()
    } catch {
      auth.clearAuth()
      return next({ name: 'Login' })
    }
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }

  if (to.name === 'Login' && auth.isAuthenticated) {
    return next({ name: 'Dashboard' })
  }

  return next()
}

router.beforeEach(async (to, _from, next) => {
  try {
    await authGuard(to, next)
  } catch (error) {
    console.error(error)
    next()
  }
})

export default router
