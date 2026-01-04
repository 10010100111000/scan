import { defineStore } from 'pinia'
import http, { request } from '@/api/http'
import { ElMessage } from 'element-plus'

export interface LoginPayload {
  username: string
  password: string
}

export interface SetupPayload extends LoginPayload {
  email?: string
}

interface UserInfo {
  userId: string
  username: string
  realName: string
  avatar: string
  roles: string[]
  token?: string | null
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('auth_token') as string | null,
    userInfo: null as UserInfo | null,
    firstRun: true,
    statusChecked: false,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
  },
  actions: {
    setToken(token: string) {
      this.token = token
      localStorage.setItem('auth_token', token)
    },
    clearAuth() {
      this.token = null
      this.userInfo = null
      localStorage.removeItem('auth_token')
    },
    async fetchAuthStatus() {
      try {
        const data = await request<{ first_run: boolean }>(http.get('/auth/status'))
        this.firstRun = data.first_run
      } catch (error) {
        console.error(error)
        this.firstRun = false
        ElMessage.error((error as Error).message)
      } finally {
        this.statusChecked = true
      }
    },
    async setup(payload: SetupPayload) {
      await request(http.post('/auth/setup', payload))
      this.firstRun = false
      ElMessage.success('管理员创建成功，请使用新账号登录')
    },
    async login(payload: LoginPayload) {
      const data = await request<{ accessToken: string }>(http.post('/auth/login', payload))
      this.setToken(data.accessToken)
      await this.fetchUserInfo()
      ElMessage.success('登录成功')
    },
    async fetchUserInfo() {
      if (!this.token) return
      try {
        const user = await request<UserInfo>(http.get('/user/info'))
        this.userInfo = user
      } catch (error) {
        this.clearAuth()
        throw error
      }
    },
    async logout() {
      try {
        await request(http.post('/auth/logout'))
      } catch (error) {
        console.warn(error)
      }
      this.clearAuth()
      this.statusChecked = true
    },
  },
})
