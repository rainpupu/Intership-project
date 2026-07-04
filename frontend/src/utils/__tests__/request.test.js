/**
 * Axios 请求封装测试
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

// Mock axios
vi.mock('axios', () => {
  const interceptors = {
    request: { use: vi.fn() },
    response: { use: vi.fn() },
  }
  return {
    default: {
      create: vi.fn(() => ({
        interceptors,
        get: vi.fn(),
        post: vi.fn(),
        put: vi.fn(),
        delete: vi.fn(),
      })),
    },
  }
})

// Mock pinia store
vi.mock('@/stores/user', () => ({
  useUserStore: vi.fn(() => ({
    token: 'test-token',
    logout: vi.fn(),
  })),
}))

// Mock router
vi.mock('@/router', () => ({
  default: {
    push: vi.fn(),
  },
}))

describe('request', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该创建 axios 实例', async () => {
    // 动态导入模块
    const { default: request } = await import('../request')

    expect(axios.create).toHaveBeenCalled()
    expect(request).toBeDefined()
  })

  it('应该配置正确的 baseURL', async () => {
    await import('../request')

    expect(axios.create).toHaveBeenCalledWith(
      expect.objectContaining({
        baseURL: '/api',
        timeout: 30000,
      })
    )
  })

  it('应该配置请求拦截器', async () => {
    await import('../request')

    // 验证请求拦截器被注册
    const createCall = axios.create.mock.results[0].value
    expect(createCall.interceptors.request.use).toHaveBeenCalled()
  })

  it('应该配置响应拦截器', async () => {
    await import('../request')

    // 验证响应拦截器被注册
    const createCall = axios.create.mock.results[0].value
    expect(createCall.interceptors.response.use).toHaveBeenCalled()
  })
})
