<template>
  <div class="detection-page">
    <!-- 左侧控制面板 -->
    <div class="control-panel">
      <h3>检测控制台</h3>
      
      <!-- 场景选择 -->
      <div class="control-section">
        <label>检测场景</label>
        <el-select v-model="selectedScene" placeholder="选择检测场景" @change="onSceneChange">
          <el-option
            v-for="scene in scenes"
            :key="scene.id"
            :label="scene.display_name"
            :value="scene.id"
          >
            <span>{{ scene.display_name }}</span>
            <span class="scene-category">{{ scene.category }}</span>
          </el-option>
        </el-select>
      </div>

      <!-- 检测模式 -->
      <div class="control-section">
        <label>检测模式</label>
        <el-radio-group v-model="detectMode">
          <el-radio-button label="single">单图检测</el-radio-button>
          <el-radio-button label="batch">批量检测</el-radio-button>
          <el-radio-button label="video">视频检测</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 参数设置 -->
      <div class="control-section">
        <label>置信度阈值</label>
        <el-slider v-model="confThreshold" :min="0.1" :max="1" :step="0.05" show-input />
      </div>

      <div class="control-section">
        <label>IoU 阈值</label>
        <el-slider v-model="iouThreshold" :min="0.1" :max="1" :step="0.05" show-input />
      </div>

      <!-- 文件上传 -->
      <div class="control-section">
        <label>上传{{ detectMode === 'video' ? '视频' : '图像' }}</label>
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :multiple="detectMode === 'batch'"
          :accept="detectMode === 'video' ? 'video/*' : 'image/*'"
          :on-change="handleFileChange"
          :file-list="fileList"
          drag
        >
          <el-icon :size="48"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            拖拽文件到此处，或<em>点击上传</em>
          </div>
        </el-upload>
      </div>

      <!-- 检测按钮 -->
      <el-button
        type="primary"
        size="large"
        :loading="detecting"
        :disabled="!selectedScene || fileList.length === 0"
        @click="startDetection"
        class="detect-btn"
      >
        <el-icon><Aim /></el-icon>开始检测
      </el-button>
    </div>

    <!-- 右侧结果展示 -->
    <div class="result-panel">
      <!-- 检测结果 -->
      <div v-if="detectionResult" class="result-content">
        <div class="result-header">
          <h3>检测结果</h3>
          <div class="result-stats">
            <el-tag type="success">目标数量: {{ detectionResult.total_objects }}</el-tag>
            <el-tag type="info">推理时间: {{ detectionResult.inference_time?.toFixed(2) }}ms</el-tag>
          </div>
        </div>

        <!-- 图像展示 -->
        <div class="image-container" v-if="detectMode !== 'video'">
          <canvas ref="canvasRef" class="detection-canvas"></canvas>
        </div>

        <!-- 视频展示 -->
        <div class="video-container" v-else>
          <video :src="detectionResult.video_url" controls class="detection-video"></video>
        </div>

        <!-- 检测详情 -->
        <div class="detection-details">
          <h4>检测详情</h4>
          <el-table :data="detectionResult.detections" stripe max-height="300">
            <el-table-column prop="class_name" label="类别" width="120" />
            <el-table-column prop="confidence" label="置信度" width="100">
              <template #default="{ row }">
                {{ (row.confidence * 100).toFixed(1) }}%
              </template>
            </el-table-column>
            <el-table-column label="位置 (x1, y1, x2, y2)">
              <template #default="{ row }">
                {{ row.bbox.map(v => v.toFixed(0)).join(', ') }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-result">
        <el-icon :size="64"><Aim /></el-icon>
        <p>上传图像并开始检测</p>
        <p class="hint">支持单图、批量、视频检测模式</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { UploadFilled, Aim } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getScenesApi, detectSingleApi, detectBatchApi, detectVideoApi } from '@/api/detection'

// 场景列表
const scenes = ref([])
const selectedScene = ref(null)
const detectMode = ref('single')
const confThreshold = ref(0.25)
const iouThreshold = ref(0.45)

// 文件上传
const fileList = ref([])
const uploadRef = ref(null)

// 检测状态
const detecting = ref(false)
const detectionResult = ref(null)
const canvasRef = ref(null)
const currentImage = ref(null)

// 加载场景列表
async function loadScenes() {
  try {
    const res = await getScenesApi()
    scenes.value = res.data || []
    if (scenes.value.length > 0) {
      selectedScene.value = scenes.value[0].id
    }
  } catch (error) {
    console.error('加载场景失败:', error)
  }
}

// 场景变更
function onSceneChange() {
  detectionResult.value = null
  fileList.value = []
}

// 文件变更
function handleFileChange(file) {
  if (detectMode.value !== 'batch') {
    fileList.value = [file]
  }
}

// 开始检测
async function startDetection() {
  if (!selectedScene.value || fileList.value.length === 0) {
    ElMessage.warning('请选择场景并上传文件')
    return
  }

  detecting.value = true
  detectionResult.value = null

  try {
    const params = {
      scene_id: selectedScene.value,
      conf_threshold: confThreshold.value,
      iou_threshold: iouThreshold.value
    }

    let res
    if (detectMode.value === 'single') {
      res = await detectSingleApi({
        ...params,
        image: fileList.value[0].raw
      })
    } else if (detectMode.value === 'batch') {
      res = await detectBatchApi({
        ...params,
        images: fileList.value.map(f => f.raw)
      })
    } else {
      res = await detectVideoApi({
        ...params,
        video: fileList.value[0].raw
      })
    }

    detectionResult.value = res.data
    ElMessage.success('检测完成')

    // 绘制检测框
    if (detectMode.value !== 'video') {
      await nextTick()
      drawDetections()
    }
  } catch (error) {
    ElMessage.error('检测失败: ' + (error.message || '未知错误'))
  } finally {
    detecting.value = false
  }
}

// 绘制检测框
function drawDetections() {
  const canvas = canvasRef.value
  if (!canvas || !detectionResult.value) return

  const ctx = canvas.getContext('2d')
  const img = new Image()
  
  // 获取上传的图像
  const file = fileList.value[0]
  if (!file) return

  img.onload = () => {
    // 设置canvas尺寸
    canvas.width = img.width
    canvas.height = img.height
    
    // 绘制图像
    ctx.drawImage(img, 0, 0)
    
    // 绘制检测框
    const detections = detectionResult.value.detections || []
    detections.forEach(det => {
      const [x1, y1, x2, y2] = det.bbox
      
      // 绘制边界框
      ctx.strokeStyle = '#409eff'
      ctx.lineWidth = 2
      ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)
      
      // 绘制标签背景
      const label = `${det.class_name} ${(det.confidence * 100).toFixed(0)}%`
      ctx.font = '14px Arial'
      const textWidth = ctx.measureText(label).width
      ctx.fillStyle = '#409eff'
      ctx.fillRect(x1, y1 - 24, textWidth + 10, 24)
      
      // 绘制标签文字
      ctx.fillStyle = '#fff'
      ctx.fillText(label, x1 + 5, y1 - 6)
    })
  }
  
  img.src = URL.createObjectURL(file.raw)
}

// 监听检测模式变化
watch(detectMode, () => {
  fileList.value = []
  detectionResult.value = null
})

onMounted(() => {
  loadScenes()
})
</script>

<style lang="scss" scoped>
.detection-page {
  display: flex;
  height: calc(100vh - #{$header-height} - 40px);
  background: $bg-color;
}

.control-panel {
  width: 320px;
  background: #fff;
  border-right: 1px solid #ebeef5;
  padding: $spacing-lg;
  overflow-y: auto;

  h3 {
    margin: 0 0 $spacing-lg;
    font-size: 18px;
    color: $text-primary;
  }

  .control-section {
    margin-bottom: $spacing-lg;

    label {
      display: block;
      margin-bottom: $spacing-sm;
      font-size: 14px;
      color: $text-regular;
    }

    .el-select,
    .el-radio-group {
      width: 100%;
    }

    .scene-category {
      float: right;
      color: $text-secondary;
      font-size: 12px;
    }
  }

  .detect-btn {
    width: 100%;
    margin-top: $spacing-md;
  }
}

.result-panel {
  flex: 1;
  padding: $spacing-lg;
  overflow-y: auto;
}

.result-content {
  background: #fff;
  border-radius: $border-radius-lg;
  padding: $spacing-lg;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-lg;

  h3 {
    margin: 0;
    font-size: 18px;
    color: $text-primary;
  }

  .result-stats {
    display: flex;
    gap: $spacing-sm;
  }
}

.image-container {
  margin-bottom: $spacing-lg;
  text-align: center;

  .detection-canvas {
    max-width: 100%;
    max-height: 500px;
    border: 1px solid #ebeef5;
    border-radius: $border-radius-md;
  }
}

.video-container {
  margin-bottom: $spacing-lg;
  text-align: center;

  .detection-video {
    max-width: 100%;
    max-height: 500px;
    border-radius: $border-radius-md;
  }
}

.detection-details {
  h4 {
    margin: 0 0 $spacing-md;
    font-size: 16px;
    color: $text-primary;
  }
}

.empty-result {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: #fff;
  border-radius: $border-radius-lg;
  color: $text-secondary;

  p {
    margin: $spacing-md 0 0;
    font-size: 16px;
  }

  .hint {
    font-size: 14px;
    color: $text-placeholder;
  }
}
</style>
<template>
  <div class="page-container">
    <h2>目标检测</h2>
    <p>Day8 将在此实现图片上传 / 检测 / 结果展示功能</p>
  </div>
</template>
