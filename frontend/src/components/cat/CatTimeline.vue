<template>
  <el-timeline class="cat-timeline">
    <el-timeline-item
      v-for="item in observations"
      :key="item.id"
      :timestamp="formatDateTime(item.observedAt)"
      placement="top"
      color="#fb923c"
    >
      <div class="timeline-card">
        <div class="timeline-title">
          <strong>{{ item.location || '校内固定观察点' }}</strong>
          <el-tag size="small" effect="plain">{{ item.healthStatus || '健康待确认' }}</el-tag>
        </div>
        <span>{{ item.moodStatus || '心情待确认' }}</span>
      </div>
    </el-timeline-item>
  </el-timeline>
</template>

<script setup lang="ts">
import type { Observation } from '@/types/cat';
import { formatDateTime } from '@/utils/formatter';

defineProps<{
  observations: Observation[];
}>();
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.cat-timeline {
  padding-left: 4px;
}

.timeline-card {
  padding: 14px;
  border: 1px solid rgba(251, 146, 60, 0.18);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.76);
}

.timeline-title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

strong {
  color: $color-text;
}

span {
  color: $color-primary-dark;
  font-size: 12px;
  font-weight: 700;
}
</style>
