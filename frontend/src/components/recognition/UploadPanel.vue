<template>
  <section class="upload-panel">
    <el-upload drag multiple :auto-upload="false" :on-change="handleChange">
      <div class="upload-inner">
        <div class="plus">＋</div>
        <h3>上传多角度猫咪照片</h3>
        <p>支持 JPG / PNG，当前阶段仅用于前端流程展示</p>
      </div>
    </el-upload>
  </section>
</template>

<script setup lang="ts">
import type { UploadFile } from 'element-plus';

const emit = defineEmits<{
  change: [files: UploadFile[]];
}>();

const selectedFiles: UploadFile[] = [];

function handleChange(file: UploadFile) {
  selectedFiles.push(file);
  emit('change', selectedFiles);
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.upload-panel :deep(.el-upload) {
  width: 100%;
}

.upload-panel :deep(.el-upload-dragger) {
  width: 100%;
  min-height: 250px;
  border: 1px dashed rgba(251, 146, 60, 0.45);
  border-radius: 22px;
  background: rgba(255, 247, 237, 0.62);
}

.upload-inner {
  display: grid;
  min-height: 220px;
  place-items: center;
  align-content: center;
  color: $color-text-secondary;
}

.plus {
  display: grid;
  width: 62px;
  height: 62px;
  place-items: center;
  border-radius: 22px;
  background: #fff;
  color: $color-primary;
  font-size: 40px;
  box-shadow: 0 14px 35px rgba(251, 146, 60, 0.16);
}

h3 {
  margin: 16px 0 8px;
  color: $color-text;
}

p {
  margin: 0;
}
</style>
