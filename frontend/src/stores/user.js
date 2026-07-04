/**
 * 用户状态管理
 *
 * 管理 JWT Token 和用户信息的持久化
 */
import { defineStore } from 'pinia'
import { loginApi, getUserInfoApi } from '@/api/auth'

const TOKEN_KEY = 'visagent_token'
const USER_KEY = 'visagent_user'

export const useUserStore = defineStore('user', {
  state: () => ({
    // JWT Token（从 localStorage 恢复）
    token: localStorage.getItem(TOKEN_KEY) || '',
    // 当前用户信息（从 localStorage 恢复）
    user: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
  }),

  getters: {
    /** 是否已登录 */
    isLoggedIn: (state) => !!state.token,
    /** 用户名 */
    username: (state) => state.user?.username || '',
    /** 头像 */
    avatar: (state) => state.user?.avatar || '',
    /** 角色列表 */
    roles: (state) => state.user?.roles || [],
    /** 是否为超级管理员 */
    isSuperuser: (state) => state.user?.is_superuser || false,
  },

  actions: {
    /**
     * 登录
     * @param {Object} credentials - { username, password }
     */
    async login(credentials) {
      const res = await loginApi(credentials)
      // 保存 Token
      this.token = res.access_token
      localStorage.setItem(TOKEN_KEY, res.access_token)
      // 保存用户信息
      this.user = res.user
      localStorage.setItem(USER_KEY, JSON.stringify(res.user))
      return res
    },

    /**
     * 获取用户信息
     */
    async fetchUserInfo() {
      try {
        const user = await getUserInfoApi()
        this.user = user
        localStorage.setItem(USER_KEY, JSON.stringify(user))
      } catch {
        this.logout()
      }
    },

    /**
     * 登出
     */
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
  },
})
