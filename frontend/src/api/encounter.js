/**
 * 猫咪识别相关 API（出现事件分析）
 */
import request from '@/utils/request'

/**
 * 分析出现事件中的猫咪图片，识别个体身份
 * POST /api/encounters/{encounter_id}/analyze
 *
 * @param {number} encounterId - 出现事件ID
 * @returns {Promise<{
 *   code: number,
 *   message: string,
 *   data: {
 *     status: string,           // "completed" | "failed"
 *     encounter_id: number,
 *     cropped_images: string[], // 裁剪后的猫咪图片URL列表
 *     candidates: Array<{       // Top 3 候选猫
 *       cat_id: number,
 *       name: string,
 *       similarity: number,     // 相似度 0~1
 *       ref_image_url: string,  // 参考图URL
 *     }>,
 *     total_images: number,     // 事件中的图片总数
 *     detected_cats: number,    // 检测到的猫咪数量
 *   }
 * }>}
 */
export function analyzeEncounterApi(encounterId) {
  return request.post(`/encounters/${encounterId}/analyze`)
}