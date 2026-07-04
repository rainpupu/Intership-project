/**
 * Axios 请求封装
 * - 统一 baseURL
 * - JWT Token 自动注入
 * - 统一错误处理（Token 过期自动跳转登录）
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import router from '@/router'

// 创建 Axios 实例
const request = axios.create({
  baseURL: '/api',        // 使用 Vite proxy 转发
  timeout: 30000,         // 30 秒超时
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 —— 注入 Token
request.interceptors.request.use(
  (config) => {
    // 从 Pinia store 获取 Token
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 —— 统一错误处理
request.interceptors.response.use(
  (response) => {
    // 直接返回 data
    return response.data
  },
  (error) => {
    const { response, config } = error
    if (response) {
      switch (response.status) {
        case 401:
          // 登录接口的 401 表示用户名或密码错误，不做 token 过期处理
          if (config?.url?.includes('/auth/login')) {
            ElMessage.error(response.data?.detail || '用户名或密码错误')
          } else {
            // 其他接口的 401 表示 Token 过期或无效
            ElMessage.error('登录已过期，请重新登录')
            const userStore = useUserStore()
            userStore.logout()
            router.push('/login')
          }
          break
        case 403:
          ElMessage.error('没有权限访问该资源')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 422:
          // Pydantic 验证错误
          const detail = response.data?.detail
          if (Array.isArray(detail)) {
            ElMessage.error(detail[0]?.msg || '请求参数错误')
          } else {
            ElMessage.error(detail || '请求参数错误')
          }
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(response.data?.detail || `请求错误 (${response.status})`)
      }
    } else {
      // 网络错误
      ElMessage.error('网络连接失败，请检查网络')
    }
    return Promise.reject(error)
  }
)

export default request
