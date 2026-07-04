<template>
  <div class="dashboard-page">
    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon" style="background: #409eff20; color: #409eff">
          <el-icon :size="32"><Aim /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.totalDetections }}</div>
          <div class="stat-label">检测次数</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon" style="background: #67c23a20; color: #67c23a">
          <el-icon :size="32"><Box /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.totalObjects }}</div>
          <div class="stat-label">检测目标</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon" style="background: #e6a23c20; color: #e6a23c">
          <el-icon :size="32"><Cpu /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.totalModels }}</div>
          <div class="stat-label">训练模型</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon" style="background: #f56c6c20; color: #f56c6c">
          <el-icon :size="32"><ChatDotRound /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.totalChats }}</div>
          <div class="stat-label">对话次数</div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="charts-row">
      <!-- 检测趋势图 -->
      <div class="chart-card">
        <div class="card-header">
          <h3>检测趋势</h3>
          <el-radio-group v-model="trendPeriod" size="small" @change="loadTrendData">
            <el-radio-button label="week">近7天</el-radio-button>
            <el-radio-button label="month">近30天</el-radio-button>
          </el-radio-group>
        </div>
        <div ref="trendChartRef" class="chart-container"></div>
      </div>

      <!-- 目标类别分布 -->
      <div class="chart-card">
        <div class="card-header">
          <h3>目标类别分布</h3>
        </div>
        <div ref="categoryChartRef" class="chart-container"></div>
      </div>
    </div>

    <div class="charts-row">
      <!-- 场景检测统计 -->
      <div class="chart-card">
        <div class="card-header">
          <h3>场景检测统计</h3>
        </div>
        <div ref="sceneChartRef" class="chart-container"></div>
      </div>

      <!-- 模型性能对比 -->
      <div class="chart-card">
        <div class="card-header">
          <h3>模型性能对比</h3>
        </div>
        <div ref="modelChartRef" class="chart-container"></div>
      </div>
    </div>

    <!-- 最近活动 -->
    <div class="recent-activities">
      <div class="card-header">
        <h3>最近活动</h3>
        <el-button type="primary" link @click="$router.push('/history')">
          查看全部<el-icon class="el-icon--right"><ArrowRight /></el-icon>
        </el-button>
      </div>
      <el-table :data="recentActivities" stripe>
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getActivityType(row.type)" size="small">
              {{ getActivityText(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column prop="time" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.time) }}
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { Aim, Box, Cpu, ChatDotRound, ArrowRight } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getDetectionTasksApi } from '@/api/detection'
import { getTrainingTasksApi } from '@/api/training'

// 统计数据
const stats = ref({
  totalDetections: 0,
  totalObjects: 0,
  totalModels: 0,
  totalChats: 0
})

// 趋势周期
const trendPeriod = ref('week')

// 图表引用
const trendChartRef = ref(null)
const categoryChartRef = ref(null)
const sceneChartRef = ref(null)
const modelChartRef = ref(null)

// 图表实例
let trendChart = null
let categoryChart = null
let sceneChart = null
let modelChart = null

// 最近活动
const recentActivities = ref([])

// 加载统计数据
async function loadStats() {
  try {
    // 加载检测任务统计
    const detectionRes = await getDetectionTasksApi({ page: 1, page_size: 1000 })
    const detections = detectionRes.data?.items || []
    stats.value.totalDetections = detectionRes.data?.total || 0
    stats.value.totalObjects = detections.reduce((sum, d) => sum + (d.total_objects || 0), 0)

    // 加载训练任务统计
    const trainingRes = await getTrainingTasksApi({ page: 1, page_size: 1000 })
    stats.value.totalModels = trainingRes.data?.total || 0

    // 模拟对话次数（实际应从API获取）
    stats.value.totalChats = 42

    // 生成最近活动
    generateRecentActivities(detections)
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 生成最近活动
function generateRecentActivities(detections) {
  const activities = []
  
  // 添加检测活动
  detections.slice(0, 5).forEach(d => {
    activities.push({
      type: 'detection',
      description: `完成${d.task_type === 'single' ? '单图' : d.task_type === 'batch' ? '批量' : '视频'}检测，发现 ${d.total_objects || 0} 个目标`,
      time: d.created_at
    })
  })

  // 按时间排序
  activities.sort((a, b) => new Date(b.time) - new Date(a.time))
  recentActivities.value = activities.slice(0, 10)
}

// 加载趋势数据
async function loadTrendData() {
  await nextTick()
  renderTrendChart()
}

// 渲染趋势图
function renderTrendChart() {
  if (!trendChartRef.value) return
  
  if (trendChart) trendChart.dispose()
  trendChart = echarts.init(trendChartRef.value)

  // 生成模拟数据
  const days = trendPeriod.value === 'week' ? 7 : 30
  const dates = []
  const values = []
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    dates.push(date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }))
    values.push(Math.floor(Math.random() * 50) + 10)
  }

  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', name: '检测次数' },
    series: [{
      type: 'line',
      data: values,
      smooth: true,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
          { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
        ])
      },
      lineStyle: { color: '#409eff' },
      itemStyle: { color: '#409eff' }
    }]
  })
}

// 渲染类别分布图
function renderCategoryChart() {
  if (!categoryChartRef.value) return
  
  if (categoryChart) categoryChart.dispose()
  categoryChart = echarts.init(categoryChartRef.value)

  categoryChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left' },
    series: [{
      type: 'pie',
      radius: '60%',
      center: ['50%', '50%'],
      data: [
        { value: 35, name: '飞机' },
        { value: 28, name: '油罐' },
        { value: 22, name: '立交桥' },
        { value: 15, name: '操场' }
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  })
}

// 渲染场景统计图
function renderSceneChart() {
  if (!sceneChartRef.value) return
  
  if (sceneChart) sceneChart.dispose()
  sceneChart = echarts.init(sceneChartRef.value)

  sceneChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: ['遥感检测', '工业检测', '农业检测', '交通检测'] },
    yAxis: { type: 'value', name: '检测次数' },
    series: [{
      type: 'bar',
      data: [120, 85, 65, 90],
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#409eff' },
          { offset: 1, color: '#79bbff' }
        ])
      }
    }]
  })
}

// 渲染模型对比图
function renderModelChart() {
  if (!modelChartRef.value) return
  
  if (modelChart) modelChart.dispose()
  modelChart = echarts.init(modelChartRef.value)

  modelChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['mAP@0.5', 'mAP@0.5:0.95'] },
    xAxis: { type: 'category', data: ['YOLOv11n', 'YOLOv11s', 'YOLOv11m', 'YOLOv11l'] },
    yAxis: { type: 'value', name: 'mAP', max: 1 },
    series: [
      {
        name: 'mAP@0.5',
        type: 'bar',
        data: [0.72, 0.78, 0.82, 0.85]
      },
      {
        name: 'mAP@0.5:0.95',
        type: 'bar',
        data: [0.55, 0.62, 0.68, 0.72]
      }
    ]
  })
}

// 活动类型
function getActivityType(type) {
  const map = {
    detection: 'primary',
    training: 'warning',
    chat: 'success'
  }
  return map[type] || 'info'
}

function getActivityText(type) {
  const map = {
    detection: '检测',
    training: '训练',
    chat: '对话'
  }
  return map[type] || type
}

// 格式化时间
function formatTime(timestamp) {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleString('zh-CN')
}

// 窗口大小变化
function handleResize() {
  trendChart?.resize()
  categoryChart?.resize()
  sceneChart?.resize()
  modelChart?.resize()
}

onMounted(async () => {
  await loadStats()
  await nextTick()
  renderTrendChart()
  renderCategoryChart()
  renderSceneChart()
  renderModelChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  categoryChart?.dispose()
  sceneChart?.dispose()
  modelChart?.dispose()
})
</script>

<style lang="scss" scoped>
.dashboard-page {
  padding: $spacing-lg;
  background: $bg-color;
  min-height: calc(100vh - #{$header-height} - 40px);
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $spacing-lg;
  margin-bottom: $spacing-lg;
}

.stat-card {
  background: #fff;
  border-radius: $border-radius-lg;
  padding: $spacing-lg;
  display: flex;
  align-items: center;
  gap: $spacing-md;
  box-shadow: $shadow-sm;

  .stat-icon {
    width: 64px;
    height: 64px;
    border-radius: $border-radius-md;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .stat-info {
    .stat-value {
      font-size: 28px;
      font-weight: 600;
      color: $text-primary;
    }

    .stat-label {
      font-size: 14px;
      color: $text-secondary;
      margin-top: $spacing-xs;
    }
  }
}

.charts-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $spacing-lg;
  margin-bottom: $spacing-lg;
}

.chart-card {
  background: #fff;
  border-radius: $border-radius-lg;
  padding: $spacing-lg;
  box-shadow: $shadow-sm;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-md;

    h3 {
      margin: 0;
      font-size: 16px;
      color: $text-primary;
    }
  }

  .chart-container {
    height: 300px;
  }
}

.recent-activities {
  background: #fff;
  border-radius: $border-radius-lg;
  padding: $spacing-lg;
  box-shadow: $shadow-sm;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-md;

    h3 {
      margin: 0;
      font-size: 16px;
      color: $text-primary;
    }
  }
}
</style>
<template>
  <div class="page-container">
    <h2>仪表盘</h2>
    <p>Day10 将在此实现 ECharts 数据可视化仪表盘</p>
  </div>
</template>
