/**
 * 公共格式化工具函数
 * 提取自各页面组件中的重复代码
 */

/**
 * 格式化时间戳为本地化字符串
 * @param {string|number|Date} timestamp - 时间戳
 * @returns {string} 格式化后的时间字符串
 */
export function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return isNaN(date.getTime()) ? '' : date.toLocaleString('zh-CN')
}

/**
 * 格式化时间戳为短时间（时:分）
 * @param {string|number|Date} timestamp - 时间戳
 * @returns {string} 短时间字符串
 */
export function formatShortTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return isNaN(date.getTime()) ? '' : date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

/**
 * 任务状态 → Element Plus Tag 类型
 * @param {string} status - 任务状态
 * @returns {string} tag type
 */
export function getStatusType(status) {
  const map = {
    pending: 'info',
    running: 'warning',
    paused: 'warning',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

/**
 * 任务状态 → 中文显示文本
 * @param {string} status - 任务状态
 * @returns {string} 中文文本
 */
export function getStatusText(status) {
  const map = {
    pending: '等待中',
    running: '运行中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return map[status] || status
}
