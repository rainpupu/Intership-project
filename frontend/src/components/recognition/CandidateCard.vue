<template>
  <article class="candidate-card">
    <img :src="candidate.image" :alt="candidate.name" />
    <div class="content">
      <div class="title">
        <strong>{{ candidate.name }}</strong>
        <el-tag size="small">{{ formatPercent(candidate.similarity) }}</el-tag>
      </div>
      <p>{{ candidate.reason }}</p>
      <span>{{ candidate.status }}</span>
    </div>
  </article>
</template>

<script setup lang="ts">
import type { RecognitionCandidate } from '@/types/recognition';
import { formatPercent } from '@/utils/formatter';

defineProps<{
  candidate: RecognitionCandidate;
}>();
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.candidate-card {
  display: grid;
  grid-template-columns: 74px 1fr;
  gap: 12px;
  padding: 12px;
  border: 1px solid rgba(251, 146, 60, 0.18);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
}

img {
  width: 74px;
  height: 74px;
  border-radius: 16px;
  object-fit: cover;
}

.title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

strong {
  color: $color-text;
}

p {
  margin: 6px 0;
  color: $color-text-secondary;
  font-size: 13px;
  line-height: 1.5;
}

span {
  color: $color-primary-dark;
  font-size: 12px;
  font-weight: 700;
}
</style>
