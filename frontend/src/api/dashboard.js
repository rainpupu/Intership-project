/**
 * Dashboard 聚合统计 API
 * 后端一次返回全部看板数据，避免前端多次请求
 */
import request from '@/utils/request'

/**
 * 获取 Dashboard 全量统计数据
 * 返回: overview / trend / scene_stats / class_distribution / training_status / recent_detections
 */
export function getDashboardStatsApi() {
  return request.get('/dashboard/stats')
}
