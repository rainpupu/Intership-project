<template>
  <main class="admin-page">
    <section class="page-head">
      <div>
        <h1 class="page-title">猫咪识别页面</h1>
        <p class="page-subtitle">管理员视角展示全平台上传、AI 识别、身份确认和保存记录流程。</p>
      </div>
    </section>

    <section class="soft-card steps-card">
      <el-steps :active="activeStep" finish-status="success" align-center>
        <el-step title="上传图片" />
        <el-step title="AI 识别" />
        <el-step title="身份确认" />
        <el-step title="保存记录" />
      </el-steps>
    </section>

    <section class="recognition-grid">
      <div class="soft-card panel">
        <h2 class="section-title">多图片上传</h2>
        <UploadPanel @change="handleUploadChange" />
      </div>

      <DetectionPreview v-if="topCandidate" :image="topCandidate.image" :confidence="analysis.confidence" />

      <div class="soft-card panel">
        <h2 class="section-title">候选猫咪 Top 3</h2>
        <div class="candidate-list">
          <CandidateCard v-for="candidate in candidates" :key="candidate.catId" :candidate="candidate" />
        </div>
      </div>

      <div class="soft-card panel ai-report">
        <h2 class="section-title">AI 分析结果</h2>
        <p>{{ analysis.summary }}</p>
        <div class="hint-grid">
          <div>
            <strong>健康提示</strong>
            <span v-for="item in analysis.healthHints" :key="item">{{ item }}</span>
          </div>
          <div>
            <strong>行为提示</strong>
            <span v-for="item in analysis.behaviorHints" :key="item">{{ item }}</span>
          </div>
        </div>

        <div class="actions">
          <el-button type="primary" round @click="confirmExisting">确认为已有猫</el-button>
          <el-button round @click="createNew">创建新猫档案</el-button>
          <el-button round @click="activeStep = 2">暂不确认</el-button>
        </div>
      </div>
    </section>

    <section class="soft-card records-card">
      <div class="records-head">
        <div>
          <h2 class="section-title">全平台最近识别记录</h2>
          <p>管理员通过 `getRecognitionRecords({ scope: 'all' })` 查看所有用户上传记录。</p>
        </div>
      </div>
      <el-table :data="records" row-key="id">
        <el-table-column label="图片" width="100">
          <template #default="{ row }">
            <img class="record-image" :src="row.image" :alt="row.catName" />
          </template>
        </el-table-column>
        <el-table-column prop="catName" label="候选猫咪" min-width="130" />
        <el-table-column prop="userId" label="上传用户" min-width="150" />
        <el-table-column label="相似度" width="110">
          <template #default="{ row }">{{ formatPercent(row.similarity) }}</template>
        </el-table-column>
        <el-table-column prop="location" label="地点" min-width="170" />
        <el-table-column prop="status" label="状态" width="110" />
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.createdAt) }}</template>
        </el-table-column>
      </el-table>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage, type UploadFile } from 'element-plus';
import {
  analyzeEncounter,
  confirmExistingCat,
  createNewCat,
  getRecognitionCandidates,
  getRecognitionRecords,
} from '@/api/recognition';
import CandidateCard from '@/components/recognition/CandidateCard.vue';
import DetectionPreview from '@/components/recognition/DetectionPreview.vue';
import UploadPanel from '@/components/recognition/UploadPanel.vue';
import type { RecognitionAnalysis, RecognitionCandidate, RecognitionRecord } from '@/types/recognition';
import { formatDateTime, formatPercent } from '@/utils/formatter';

const activeStep = ref(1);
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
  activeStep.value = files.length > 0 ? 2 : 1;
}

async function confirmExisting() {
  if (!topCandidate.value) {
    return;
  }

  await confirmExistingCat(topCandidate.value.catId);
  activeStep.value = 4;
  ElMessage.success('已确认匹配已有猫，等待保存记录接口接入。');
}

async function createNew() {
  await createNewCat();
  activeStep.value = 4;
  ElMessage.success('已进入创建新猫档案流程占位。');
}

onMounted(async () => {
  candidates.value = await getRecognitionCandidates();
  records.value = await getRecognitionRecords({ scope: 'all' });
  Object.assign(analysis, await analyzeEncounter());
});
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.admin-page {
  padding: 28px;
}

.page-head {
  margin-bottom: 22px;
}

.steps-card {
  margin-bottom: 22px;
  padding: 22px;
}

.recognition-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(340px, 0.9fr);
  gap: 22px;
  align-items: start;
  margin-bottom: 22px;
}

.panel,
.records-card {
  padding: 20px;
}

.candidate-list {
  display: grid;
  gap: 12px;
}

.ai-report {
  background:
    radial-gradient(circle at 88% 12%, rgba(96, 165, 250, 0.22), transparent 34%),
    rgba(255, 255, 255, 0.86);
}

.ai-report p,
.records-head p {
  color: $color-text-secondary;
  line-height: 1.8;
}

.hint-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin: 18px 0;
}

.hint-grid div {
  display: grid;
  gap: 8px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(255, 247, 237, 0.74);
}

strong {
  color: $color-text;
}

.hint-grid span {
  color: $color-text-secondary;
  font-size: 13px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.record-image {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  object-fit: cover;
}

@media (max-width: 1100px) {
  .recognition-grid,
  .hint-grid {
    grid-template-columns: 1fr;
  }
}
</style>
