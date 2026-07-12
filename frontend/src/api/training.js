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

/**
 * 上传训练好的模型文件
 * @param {Object} data - { scene_id, model_file, version, model_name, model_type, description, is_default }
 */
export function uploadModelApi(data) {
  const formData = new FormData()
  formData.append('scene_id', data.scene_id)
  formData.append('model_file', data.model_file)
  formData.append('version', data.version)
  formData.append('model_name', data.model_name)
  formData.append('model_type', data.model_type || 'yolov11n')
  formData.append('description', data.description || '')
  formData.append('is_default', data.is_default ?? true)
  return request.post('/training/models/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * VOC XML → YOLO TXT 格式转换
 * @param {Object} data - { voc_file, class_names }
 */
export function convertVocToYoloApi(data) {
  const formData = new FormData()
  formData.append('voc_file', data.voc_file)
  formData.append('class_names', data.class_names)
  return request.post('/training/datasets/convert/voc-to-yolo', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * COCO JSON → YOLO TXT 格式转换
 * @param {Object} data - { coco_file, image_dir, output_dir }
 */
export function convertCocoToYoloApi(data) {
  const formData = new FormData()
  formData.append('coco_file', data.coco_file)
  formData.append('image_dir', data.image_dir)
  formData.append('output_dir', data.output_dir)
  return request.post('/training/datasets/convert/coco-to-yolo', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * LabelMe JSON → YOLO TXT 格式转换
 * @param {Object} data - { labelme_file, class_names }
 */
export function convertLabelmeToYoloApi(data) {
  const formData = new FormData()
  formData.append('labelme_file', data.labelme_file)
  formData.append('class_names', data.class_names)
  return request.post('/training/datasets/convert/labelme-to-yolo', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// ══════════════════════════════════════════════════════════════
// 模型版本管理
// ══════════════════════════════════════════════════════════════

/**
 * 获取模型版本列表（分页）
 * @param {Object} params - { scene_id, status, page, page_size }
 */
export function getModelListApi(params) {
  return request.get('/training/models', { params })
}

/**
 * 获取模型版本详情
 * @param {number} modelId
 */
export function getModelDetailApi(modelId) {
  return request.get(`/training/models/${modelId}`)
}

/**
 * 更新模型版本信息
 * @param {number} modelId
 * @param {Object} data - { version, model_name, description, status, is_default }
 */
export function updateModelApi(modelId, data) {
  const formData = new FormData()
  if (data.version !== undefined) formData.append('version', data.version)
  if (data.model_name !== undefined) formData.append('model_name', data.model_name)
  if (data.description !== undefined) formData.append('description', data.description)
  if (data.status !== undefined) formData.append('status', data.status)
  if (data.is_default !== undefined) formData.append('is_default', data.is_default)
  return request.put(`/training/models/${modelId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * 删除模型版本
 * @param {number} modelId
 * @param {boolean} hardDelete - true=硬删除（删文件+记录），false=软删除
 */
export function deleteModelApi(modelId, hardDelete = false) {
  const formData = new FormData()
  formData.append('hard_delete', hardDelete)
  return request.delete(`/training/models/${modelId}`, {
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/**
 * 设置模型为场景默认模型
 * @param {number} modelId
 */
export function setDefaultModelApi(modelId) {
  return request.put(`/training/models/${modelId}/set-default`)
}

/**
 * 下载模型文件
 * @param {number} modelId
 * @returns {Promise<Blob>} 模型文件 Blob
 */
export function downloadModelApi(modelId) {
  return request.get(`/training/models/${modelId}/download`, {
    responseType: 'blob'
  })
}
