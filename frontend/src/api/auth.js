/**
 * 认证相关 API
 */
import request from '@/utils/request'

/**
 * 注册
 * @param {Object} data - { username, email, password }
 */
export function registerApi(data) {
  return request.post('/auth/register', data)
}

/**
 * 登录
 * @param {Object} data - { username, password }
 * @returns {Promise} - { access_token, token_type, user }
 */
export function loginApi(data) {
  return request.post('/auth/login', data)
}

/**
 * 获取当前用户信息（需携带 Token）
 */
export function getUserInfoApi() {
  return request.get('/auth/me')
}
