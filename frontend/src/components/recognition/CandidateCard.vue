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
  grid-template-columns: 180px minmax(0, 1fr);
  gap: 16px;
  align-items: center;
  padding: 14px 16px;
  border: 1px solid rgba(251, 146, 60, 0.18);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
}

img {
  width: 180px;
  height: 124px;
  border-radius: 16px;
  object-fit: contain;
  background: rgba(255, 247, 237, 0.82);
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

@media (max-width: 620px) {
  .candidate-card {
    grid-template-columns: 112px minmax(0, 1fr);
    gap: 12px;
    padding: 12px;
  }

  img {
    width: 112px;
    height: 92px;
  }
}
</style>
