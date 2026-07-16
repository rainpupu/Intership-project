<template>
  <section class="chart-card">
    <div class="chart-header">
      <div>
        <h3>{{ title }}</h3>
        <p>{{ description }}</p>
      </div>
      <el-tag effect="plain">ECharts</el-tag>
    </div>
    <div ref="chartRef" class="chart"></div>
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent } from 'echarts/components';
import * as echarts from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([GridComponent, TooltipComponent, LineChart, CanvasRenderer]);

const props = defineProps<{
  title: string;
  description: string;
  labels: string[];
  values: number[];
}>();

const chartRef = ref<HTMLDivElement>();
let chartInstance: echarts.EChartsType | null = null;

function renderChart() {
  if (!chartRef.value) {
    return;
  }

  chartInstance ??= echarts.init(chartRef.value);
  chartInstance.setOption({
    color: ['#fb923c'],
    grid: {
      left: 28,
      right: 20,
      top: 24,
      bottom: 28,
    },
    tooltip: {
      trigger: 'axis',
    },
    xAxis: {
      type: 'category',
      data: props.labels,
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#fed7aa' } },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: 'rgba(251, 146, 60, 0.12)' } },
    },
    series: [
      {
        type: 'line',
        smooth: true,
        data: props.values,
        areaStyle: {
          color: 'rgba(251, 146, 60, 0.18)',
        },
      },
    ],
  });
}

function resizeChart() {
  chartInstance?.resize();
}

onMounted(() => {
  renderChart();
  window.addEventListener('resize', resizeChart);
});

watch(() => [props.labels, props.values], renderChart, { deep: true });

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart);
  chartInstance?.dispose();
});
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;
@use '@/assets/styles/mixins' as *;

.chart-card {
  @include card-shell(22px);
  padding: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

h3,
p {
  margin: 0;
}

h3 {
  color: $color-text;
}

p {
  margin-top: 6px;
  color: $color-text-secondary;
}

.chart {
  width: 100%;
  height: 260px;
}
</style>
