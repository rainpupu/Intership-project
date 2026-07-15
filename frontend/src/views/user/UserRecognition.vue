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
          <el-button type="primary" round :loading="analyzing" @click="handleAnalyze">开始识别</el-button>
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
      <el-table :data="records" row-key="id">
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
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage, type UploadFile } from 'element-plus';
import {
  analyzeEncounter,
  getRecognitionCandidates,
  getRecognitionRecords,
  uploadEncounterImages,
} from '@/api/recognition';
import PageContainer from '@/components/common/PageContainer.vue';
import CandidateCard from '@/components/recognition/CandidateCard.vue';
import DetectionPreview from '@/components/recognition/DetectionPreview.vue';
import UploadPanel from '@/components/recognition/UploadPanel.vue';
import { useUserStore } from '@/stores/user';
import type { RecognitionAnalysis, RecognitionCandidate, RecognitionRecord } from '@/types/recognition';
import { formatDateTime, formatPercent } from '@/utils/formatter';

const userStore = useUserStore();
const selectedFiles = ref<UploadFile[]>([]);
const analyzing = ref(false);
const candidates = ref<RecognitionCandidate[]>([]);
const records = ref<RecognitionRecord[]>([]);
const analysis = reactive<RecognitionAnalysis>({
  confidence: 0,
  healthHints: [],
  behaviorHints: [],
  summary: '',
});

const topCandidate = computed(() => candidates.value[0]);

function handleUploadChange(files: UploadFile[]) {
  selectedFiles.value = files;
}

async function handleAnalyze() {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请先选择至少一张图片');
    return;
  }

  analyzing.value = true;
  try {
    const rawFiles = selectedFiles.value.map((item) => item.raw).filter(Boolean) as File[];
    await uploadEncounterImages(rawFiles);
    candidates.value = await getRecognitionCandidates();
    Object.assign(analysis, await analyzeEncounter());
    ElMessage.success('识别完成，当前为 Mock 结果');
  } finally {
    analyzing.value = false;
  }
}

async function fetchMineRecords() {
  records.value = await getRecognitionRecords({
    scope: 'mine',
    userId: userStore.profile?.id,
  });
}

onMounted(async () => {
  await fetchMineRecords();
  candidates.value = await getRecognitionCandidates();
  Object.assign(analysis, await analyzeEncounter());
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
