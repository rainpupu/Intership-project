<template>
  <section class="preview">
    <div class="image-wrap">
      <img :src="image" alt="识别预览" />
    </div>
    <div class="caption">
      <div class="caption-head">
        <strong>AI 识别预览</strong>
        <el-tag type="success" effect="light">检测完成</el-tag>
      </div>
      <p>系统已生成 YOLO 检测缩略图，可用于快速核对识别目标。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  image: string;
  confidence: number;
}>();
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;
@use '@/assets/styles/mixins' as *;

.preview {
  @include card-shell(22px);
  display: grid;
  grid-template-columns: 116px minmax(0, 1fr);
  gap: 14px;
  align-items: center;
  padding: 14px;
}

.image-wrap {
  position: relative;
  width: 116px;
  height: 88px;
  overflow: hidden;
  border: 1px solid rgba(251, 146, 60, 0.16);
  border-radius: 16px;
  background: rgba(255, 247, 237, 0.82);
}

img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.caption {
  min-width: 0;
}

.caption-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

strong {
  color: $color-text;
}

p {
  margin: 8px 0 0;
  color: $color-text-secondary;
  line-height: 1.6;
}

@media (max-width: 620px) {
  .preview {
    grid-template-columns: 1fr;
  }

  .image-wrap {
    width: 100%;
    height: 150px;
  }
}
</style>
