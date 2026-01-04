import axios from 'axios'

export interface ApiResponse<T = unknown> {
  code: number
  data: T
  message: string
}

const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.message || error.response?.data?.detail || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export async function request<T>(promise: Promise<{ data: ApiResponse<T> }>): Promise<T> {
  const { data } = await promise
  if (data && typeof data === 'object' && 'code' in data) {
    const payload = data as ApiResponse<T>
    if (payload.code !== 0) {
      throw new Error(payload.message || '请求失败')
    }
    return payload.data
  }
  return data as T
}

export default http
