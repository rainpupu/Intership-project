<template>
  <section class="upload-panel">
    <el-upload
      v-if="!selectedFiles.length"
      class="empty-uploader"
      drag
      multiple
      :auto-upload="false"
      :show-file-list="false"
      :on-change="handleChange"
    >
      <div class="upload-inner">
        <div class="plus">＋</div>
        <h3>上传多角度猫咪照片</h3>
        <p>支持 JPG / PNG，上传后调用本地 YOLO 模型识别</p>
      </div>
    </el-upload>

    <div v-else class="uploaded-state">
      <div class="uploaded-head">
        <div>
          <strong>已上传图片</strong>
          <span>{{ selectedFiles.length }} 张，确认后可开始识别</span>
        </div>
        <el-upload class="compact-uploader" multiple :auto-upload="false" :show-file-list="false" :on-change="handleChange">
          <el-button class="mini-upload-button" round>＋ 继续上传</el-button>
        </el-upload>
      </div>

      <div class="preview-list">
        <article v-for="file in selectedFiles" :key="file.uid" class="preview-item">
          <img :src="getPreviewUrl(file)" :alt="file.name" />
          <div class="file-meta">
            <strong>{{ file.name }}</strong>
            <span>{{ formatFileSize(file.size) }}</span>
          </div>
          <div class="preview-actions">
            <el-button size="small" round @click="openPreview(file)">查看</el-button>
            <el-button size="small" round @click="removeSelected(file)">移除</el-button>
          </div>
        </article>
        <div class="inline-upload">
          <el-upload class="inline-uploader" multiple :auto-upload="false" :show-file-list="false" :on-change="handleChange">
            <button type="button" class="inline-upload-button">
              <span>＋</span>
              <em>添加图片</em>
            </button>
          </el-upload>
        </div>
      </div>
    </div>

    <el-dialog v-model="previewVisible" title="图片内容预览" width="min(820px, 92vw)" append-to-body>
      <img v-if="previewUrl" class="dialog-image" :src="previewUrl" alt="上传图片预览" />
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue';
import type { UploadFile } from 'element-plus';

interface LocalUploadFile extends UploadFile {
  previewUrl?: string;
}

const emit = defineEmits<{
  change: [files: UploadFile[]];
}>();

const selectedFiles = ref<LocalUploadFile[]>([]);
const previewVisible = ref(false);
const previewUrl = ref('');

function handleChange(file: UploadFile) {
  const localFile = file as LocalUploadFile;
  if (!localFile.previewUrl && localFile.raw) {
    localFile.previewUrl = URL.createObjectURL(localFile.raw);
  }

  if (!selectedFiles.value.some((item) => item.uid === file.uid)) {
    selectedFiles.value.push(localFile);
  }
  emit('change', selectedFiles.value);
}

function removeSelected(file: LocalUploadFile) {
  if (file.previewUrl?.startsWith('blob:')) {
    URL.revokeObjectURL(file.previewUrl);
  }

  selectedFiles.value = selectedFiles.value.filter((item) => item.uid !== file.uid);
  emit('change', selectedFiles.value);
}

function getPreviewUrl(file: LocalUploadFile) {
  if (file.previewUrl) {
    return file.previewUrl;
  }

  if (file.url) {
    return file.url;
  }

  return '';
}

function openPreview(file: LocalUploadFile) {
  previewUrl.value = getPreviewUrl(file);
  previewVisible.value = true;
}

function formatFileSize(size?: number) {
  if (!size) {
    return '未知大小';
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }

  return `${(size / 1024 / 1024).toFixed(2)} MB`;
}

onBeforeUnmount(() => {
  selectedFiles.value.forEach((file) => {
    if (file.previewUrl?.startsWith('blob:')) {
      URL.revokeObjectURL(file.previewUrl);
    }
  });
});
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.empty-uploader :deep(.el-upload),
.inline-uploader :deep(.el-upload) {
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

.uploaded-state {
  min-height: 190px;
  padding: 14px;
  border: 1px dashed rgba(251, 146, 60, 0.35);
  border-radius: 22px;
  background: rgba(255, 247, 237, 0.46);
}

.uploaded-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.uploaded-head strong,
.uploaded-head span {
  display: block;
}

.uploaded-head strong {
  color: $color-text;
}

.uploaded-head span {
  margin-top: 4px;
  color: $color-text-secondary;
  font-size: 12px;
}

.mini-upload-button {
  border-color: rgba(251, 146, 60, 0.28);
  color: $color-primary;
}

.preview-list {
  display: grid;
  gap: 10px;
}

.preview-item {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 12px;
  border: 1px solid rgba(251, 146, 60, 0.16);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.86);
}

.preview-actions {
  display: flex;
  gap: 8px;
}

.preview-item img {
  width: 64px;
  height: 64px;
  border-radius: 14px;
  object-fit: cover;
}

.preview-item strong,
.preview-item span {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-item strong {
  color: $color-text;
  font-size: 14px;
}

.preview-item span {
  margin-top: 4px;
  color: $color-text-secondary;
  font-size: 12px;
}

.inline-upload {
  display: none;
}

.inline-upload-button {
  display: grid;
  width: 100%;
  min-height: 58px;
  place-items: center;
  align-content: center;
  border: 1px dashed rgba(251, 146, 60, 0.4);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.62);
  color: $color-primary;
  cursor: pointer;
}

.inline-upload-button span {
  font-size: 24px;
  line-height: 1;
}

.inline-upload-button em {
  margin-top: 2px;
  font-style: normal;
  font-size: 12px;
}

.dialog-image {
  display: block;
  width: 100%;
  max-height: 72vh;
  border-radius: 16px;
  object-fit: contain;
  background: #fff7ed;
}

@media (max-width: 720px) {
  .uploaded-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .preview-item {
    grid-template-columns: 58px minmax(0, 1fr);
  }

  .preview-actions {
    grid-column: 1 / -1;
  }

  .inline-upload {
    display: block;
  }
}
</style>
