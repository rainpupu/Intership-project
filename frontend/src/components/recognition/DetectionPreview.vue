<template>
  <section class="preview">
    <div class="image-wrap">
      <img :src="image" alt="识别预览" />
      <span class="box"></span>
      <el-tag class="confidence" type="success">置信度 {{ confidenceText }}</el-tag>
    </div>
    <div class="caption">
      <strong>AI 识别预览</strong>
      <p>已检测到 1 只猫，系统正在比对历史档案与多角度参考图。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { formatPercent } from '@/utils/formatter';

const props = defineProps<{
  image: string;
  confidence: number;
}>();

const confidenceText = computed(() => formatPercent(props.confidence));
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;
@use '@/assets/styles/mixins' as *;

.preview {
  @include card-shell(22px);
  overflow: hidden;
}

.image-wrap {
  position: relative;
  aspect-ratio: 4 / 3;
  background: $color-primary-light;
}

img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.box {
  position: absolute;
  inset: 22% 25% 17% 26%;
  border: 3px solid #22c55e;
  border-radius: 18px;
  box-shadow: 0 0 0 999px rgba(0, 0, 0, 0.08);
}

.confidence {
  position: absolute;
  top: 14px;
  left: 14px;
}

.caption {
  padding: 16px;
}

strong {
  color: $color-text;
}

p {
  margin: 8px 0 0;
  color: $color-text-secondary;
  line-height: 1.6;
}
</style>
