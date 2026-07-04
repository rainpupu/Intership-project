/**
 * 历史记录相关 API
 */
import request from '@/utils/request'

/**
 * 获取检测历史记录
 * @param {Object} params - { scene_id, page, page_size }
 */
export function getDetectionHistoryApi(params) {
  return request.get('/detection/tasks', { params })
}

/**
 * 获取检测统计信息
 * @param {Object} params - { scene_id, start_date, end_date }
 */
export function getDetectionStatisticsApi(params) {
  return request.get('/detection/statistics', { params })
}

/**
 * 获取训练历史记录
 * @param {Object} params - { scene_id, status, page, page_size }
 */
export function getTrainingHistoryApi(params) {
  return request.get('/training/tasks', { params })
}
