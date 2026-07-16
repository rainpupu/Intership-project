<template>
  <PageContainer>
    <section class="recognition-head">
      <div>
        <h1 class="page-title">我的识别</h1>
        <p class="page-subtitle">普通用户可以上传图片进行识别，并只查看自己曾上传的相关记录。</p>
      </div>
      <el-tag size="large" effect="plain">当前用户：{{ userStore.displayName }}</el-tag>
    </section>

    <section class="recognition-grid">
      <div class="soft-card panel">
        <div class="panel-head">
          <div>
            <h2 class="section-title">上传图片识别</h2>
            <p>当前不会真实上传文件，后续会替换为 FastAPI 文件上传接口。</p>
          </div>
          <el-button type="primary" round :loading="analyzing" @click="analyzeSelectedImages">开始识别</el-button>
        </div>
        <UploadPanel @change="handleUploadChange" />
      </div>

      <div class="result-stack">
        <DetectionPreview v-if="topCandidate" :image="topCandidate.image" :confidence="analysis.confidence" />
        <div class="soft-card panel">
          <h2 class="section-title">本次候选结果</h2>
          <div class="candidate-list">
            <CandidateCard v-for="candidate in candidates" :key="candidate.catId" :candidate="candidate" />
          </div>
        </div>
      </div>
    </section>

    <section class="soft-card records-card">
      <div class="panel-head">
        <div>
          <h2 class="section-title">我的历史识别记录</h2>
          <p>这里通过 `getRecognitionRecords({ scope: 'mine', userId })` 获取，后端接入后按账号隔离数据。</p>
        </div>
      </div>
      <DataState
        v-if="recordsLoading"
        type="loading"
        :rows="4"
      />
      <DataState
        v-else-if="recordsError"
        type="error"
        :description="recordsError"
        action-text="重新加载"
        @retry="fetchMineRecords"
      />
      <EmptyState
        v-else-if="records.length === 0"
        title="暂无识别记录"
        description="上传猫咪图片并完成识别后，记录会显示在这里。"
      />
      <el-table v-else :data="records" row-key="id">
        <el-table-column label="识别图片" width="110">
          <template #default="{ row }">
            <img class="record-image" :src="row.image" :alt="row.catName" />
          </template>
        </el-table-column>
        <el-table-column prop="catName" label="候选猫咪" min-width="130" />
        <el-table-column label="相似度" width="110">
          <template #default="{ row }">{{ formatPercent(row.similarity) }}</template>
        </el-table-column>
        <el-table-column prop="location" label="上传/发现地点" min-width="170" />
        <el-table-column prop="status" label="状态" width="110" />
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.createdAt) }}</template>
        </el-table-column>
      </el-table>
    </section>
  </PageContainer>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { getRecognitionRecords } from '@/api/recognition';
import PageContainer from '@/components/common/PageContainer.vue';
import DataState from '@/components/common/DataState.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import CandidateCard from '@/components/recognition/CandidateCard.vue';
import DetectionPreview from '@/components/recognition/DetectionPreview.vue';
import UploadPanel from '@/components/recognition/UploadPanel.vue';
import { useRecognitionFlow } from '@/composables/useRecognitionFlow';
import { useUserStore } from '@/stores/user';
import type { RecognitionRecord } from '@/types/recognition';
import { formatDateTime, formatPercent } from '@/utils/formatter';

const userStore = useUserStore();
const records = ref<RecognitionRecord[]>([]);
const recordsLoading = ref(false);
const recordsError = ref('');
const {
  analysis,
  analyzing,
  candidates,
  topCandidate,
  analyzeSelectedImages,
  handleUploadChange,
  loadRecognitionPreview,
} = useRecognitionFlow();

async function fetchMineRecords() {
  recordsLoading.value = true;
  recordsError.value = '';
  try {
    records.value = await getRecognitionRecords({
      scope: 'mine',
      userId: userStore.profile?.id,
    });
  } catch {
    recordsError.value = '个人识别记录加载失败，请稍后重试。';
  } finally {
    recordsLoading.value = false;
  }
}

onMounted(async () => {
  await fetchMineRecords();
  await loadRecognitionPreview();
});
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.recognition-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
}

.recognition-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 410px;
  gap: 22px;
  align-items: start;
  margin-bottom: 22px;
}

.panel,
.records-card {
  padding: 20px;
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.panel-head p {
  margin: -8px 0 0;
  color: $color-text-secondary;
  line-height: 1.6;
}

.result-stack {
  display: grid;
  gap: 18px;
}

.candidate-list {
  display: grid;
  gap: 12px;
}

.record-image {
  width: 58px;
  height: 58px;
  border-radius: 14px;
  object-fit: cover;
}

@media (max-width: 980px) {
  .recognition-head,
  .panel-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .recognition-grid {
    grid-template-columns: 1fr;
  }
}
</style>
