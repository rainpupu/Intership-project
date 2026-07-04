/**
 * 训练相关 API
 */
import request from '@/utils/request'

/**
 * 创建训练任务
 * @param {Object} data - 训练配置
 */
export function createTrainingTaskApi(data) {
  const formData = new FormData()
  Object.keys(data).forEach(key => {
    formData.append(key, data[key])
  })
  return request.post('/training/tasks', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * 启动训练任务
 * @param {number} taskId
 */
export function startTrainingApi(taskId) {
  return request.post(`/training/tasks/${taskId}/start`)
}

/**
 * 暂停训练任务
 * @param {number} taskId
 */
export function pauseTrainingApi(taskId) {
  return request.post(`/training/tasks/${taskId}/pause`)
}

/**
 * 取消训练任务
 * @param {number} taskId
 */
export function cancelTrainingApi(taskId) {
  return request.post(`/training/tasks/${taskId}/cancel`)
}

/**
 * 获取训练任务列表
 * @param {Object} params - { scene_id, status, page, page_size }
 */
export function getTrainingTasksApi(params) {
  return request.get('/training/tasks', { params })
}

/**
 * 获取训练任务详情
 * @param {number} taskId
 */
export function getTrainingTaskApi(taskId) {
  return request.get(`/training/tasks/${taskId}`)
}

/**
 * 获取训练状态
 * @param {number} taskId
 */
export function getTrainingStatusApi(taskId) {
  return request.get(`/training/tasks/${taskId}/status`)
}

/**
 * 获取训练指标
 * @param {number} taskId
 */
export function getTrainingMetricsApi(taskId) {
  return request.get(`/training/tasks/${taskId}/metrics`)
}

/**
 * 验证数据集
 * @param {Object} data - { images_dir, labels_dir, class_names }
 */
export function validateDatasetApi(data) {
  const formData = new FormData()
  formData.append('images_dir', data.images_dir)
  formData.append('labels_dir', data.labels_dir)
  formData.append('class_names', data.class_names)
  return request.post('/training/datasets/validate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * 划分数据集
 * @param {Object} data - { images_dir, labels_dir, output_dir, train_ratio, val_ratio, test_ratio }
 */
export function splitDatasetApi(data) {
  const formData = new FormData()
  Object.keys(data).forEach(key => {
    formData.append(key, data[key])
  })
  return request.post('/training/datasets/split', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * 生成 data.yaml
 * @param {Object} data - { output_path, class_names, dataset_dir }
 */
export function generateDataYamlApi(data) {
  const formData = new FormData()
  formData.append('output_path', data.output_path)
  formData.append('class_names', data.class_names)
  formData.append('dataset_dir', data.dataset_dir)
  return request.post('/training/datasets/generate-yaml', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}
