/**
 * 对话相关 API
 */
import request from '@/utils/request'

/**
 * 创建对话会话
 * @param {Object} data - { title }
 */
export function createSessionApi(data) {
  return request.post('/chat/sessions', data)
}

/**
 * 获取会话列表
 * @param {Object} params - { page, page_size }
 */
export function getSessionsApi(params) {
  return request.get('/chat/sessions', { params })
}

/**
 * 获取对话历史
 * @param {number} sessionId
 * @param {Object} params - { limit }
 */
export function getMessagesApi(sessionId, params) {
  return request.get(`/chat/sessions/${sessionId}/messages`, { params })
}

/**
 * 删除会话
 * @param {number} sessionId
 */
export function deleteSessionApi(sessionId) {
  return request.delete(`/chat/sessions/${sessionId}`)
}
