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
            <p>上传后调用本地 YOLO 模型识别。</p>
          </div>
          <el-button type="primary" round :loading="analyzing" @click="handleAnalyze">开始识别</el-button>
        </div>
        <UploadPanel @change="handleUploadChange" />
      </div>

      <div class="result-stack">
        <div class="soft-card panel">
          <h2 class="section-title">本次候选结果</h2>
          <div v-if="candidates.length" class="candidate-list">
            <CandidateCard v-for="candidate in candidates" :key="candidate.catId" :candidate="candidate" />
            <div v-if="latestRecognizedRecord && canSubmitClue(latestRecognizedRecord)" class="clue-cta">
              <div>
                <strong>这是校园里拍到的猫吗？</strong>
                <p>填写地点后提交为校园猫线索，管理员确认后才会写入猫咪档案。</p>
              </div>
              <el-button type="primary" round @click="openClueDialog(latestRecognizedRecord)">提交校园线索</el-button>
            </div>
          </div>
          <EmptyState
            v-else
            title="暂无候选结果"
            description="上传图片并点击开始识别后，候选猫咪会显示在这里。"
          />
        </div>
      </div>
    </section>

    <section class="soft-card records-card">
      <div class="panel-head">
        <div>
          <h2 class="section-title">我的历史识别记录</h2>
          <p>当前账号的历史识别记录如下，普通用户仅可查看本人上传的数据。</p>
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
        <el-table-column label="匹配结果" width="120">
          <template #default="{ row }">
            <el-tag :type="matchTagType(row)" effect="light">{{ matchStatusText(row) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="healthStatus" label="健康" width="110" />
        <el-table-column prop="moodStatus" label="心情" width="110" />
        <el-table-column prop="location" label="上传/发现地点" min-width="170" />
        <el-table-column prop="status" label="状态" width="110" />
        <el-table-column label="时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.createdAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button v-if="canSubmitClue(row)" link type="primary" @click="openClueDialog(row)">
              提交线索
            </el-button>
            <span v-else class="muted-action">-</span>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <el-dialog v-model="clueDialogVisible" title="提交校园猫线索" width="520px">
      <div v-if="selectedRecord" class="clue-preview">
        <img :src="selectedRecord.image" :alt="selectedRecord.catName" />
        <div>
          <strong>{{ selectedRecord.catName }}</strong>
          <p>健康：{{ selectedRecord.healthStatus || '待确认' }} · 心情：{{ selectedRecord.moodStatus || '待确认' }}</p>
        </div>
      </div>
      <el-form label-width="92px">
        <el-form-item label="拍摄地点" required>
          <el-input v-model="clueForm.location" placeholder="例如：图书馆北门、三号楼花坛" />
        </el-form-item>
        <el-form-item label="拍摄时间">
          <el-date-picker
            v-model="clueForm.observedAt"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            placeholder="默认当前时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="补充说明">
          <el-input
            v-model="clueForm.userRemark"
            type="textarea"
            :rows="3"
            placeholder="例如：看起来受伤、经常在这里出现、疑似同一只猫"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="clueDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submittingClue" @click="handleSubmitClue">提交线索</el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { getRecognitionRecords, submitCampusClue } from '@/api/recognition';
import PageContainer from '@/components/common/PageContainer.vue';
import DataState from '@/components/common/DataState.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import CandidateCard from '@/components/recognition/CandidateCard.vue';
import UploadPanel from '@/components/recognition/UploadPanel.vue';
import { useRecognitionFlow } from '@/composables/useRecognitionFlow';
import { useUserStore } from '@/stores/user';
import type { RecognitionRecord } from '@/types/recognition';
import { formatDateTime } from '@/utils/formatter';

const userStore = useUserStore();
const records = ref<RecognitionRecord[]>([]);
const recordsLoading = ref(false);
const recordsError = ref('');
const clueDialogVisible = ref(false);
const submittingClue = ref(false);
const selectedRecord = ref<RecognitionRecord | null>(null);
const clueForm = reactive({
  location: '',
  observedAt: '',
  userRemark: '',
});
const {
  analyzing,
  candidates,
  analyzeSelectedImages,
  handleUploadChange,
} = useRecognitionFlow();

const latestRecognizedRecord = computed(() => {
  return records.value.find((record) => record.status === '个人识别') || null;
});

function canSubmitClue(record: RecognitionRecord) {
  return !['线索待审核', '已确认', '已建档', '未检测到'].includes(record.status);
}

function matchStatusText(record: RecognitionRecord) {
  if (record.modelType === 'individual' || (record.catId && !record.catId.startsWith('breed-'))) return '已匹配';
  if (record.modelType === 'new') return '未匹配';
  if (record.modelType === 'breed') return '仅识别品种';
  return '待确认';
}

function matchTagType(record: RecognitionRecord) {
  if (record.modelType === 'individual' || (record.catId && !record.catId.startsWith('breed-'))) return 'success';
  if (record.modelType === 'new') return 'warning';
  return 'info';
}

async function fetchMineRecords() {
  recordsLoading.value = true;
  recordsError.value = '';
  try {
    records.value = await getRecognitionRecords({
      scope: 'mine',
    });
  } catch {
    recordsError.value = '个人识别记录加载失败，请稍后重试。';
  } finally {
    recordsLoading.value = false;
  }
}

async function handleAnalyze() {
  const success = await analyzeSelectedImages();
  if (success) {
    await fetchMineRecords();
  }
}

function openClueDialog(record: RecognitionRecord) {
  selectedRecord.value = record;
  clueForm.location = record.location && record.location !== '用户上传' ? record.location : '';
  clueForm.observedAt = new Date().toISOString().slice(0, 19);
  clueForm.userRemark = record.userRemark || '';
  clueDialogVisible.value = true;
}

async function handleSubmitClue() {
  if (!selectedRecord.value) return;
  if (!clueForm.location.trim()) {
    ElMessage.warning('请填写校园拍摄地点');
    return;
  }

  submittingClue.value = true;
  try {
    await submitCampusClue(selectedRecord.value.id, {
      location: clueForm.location.trim(),
      observedAt: clueForm.observedAt || undefined,
      userRemark: clueForm.userRemark.trim() || undefined,
    });
    clueDialogVisible.value = false;
    ElMessage.success('校园猫线索已提交，等待管理员确认');
    await fetchMineRecords();
  } finally {
    submittingClue.value = false;
  }
}

onMounted(async () => {
  await fetchMineRecords();
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
  grid-template-columns: minmax(0, 1fr);
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

.clue-cta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid rgba(251, 146, 60, 0.2);
  border-radius: 16px;
  background: rgba(255, 247, 237, 0.78);
}

.clue-cta p,
.clue-preview p {
  margin: 5px 0 0;
  color: $color-text-secondary;
  font-size: 13px;
}

.clue-preview {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  margin-bottom: 18px;
}

.clue-preview img {
  width: 72px;
  height: 72px;
  border-radius: 14px;
  object-fit: cover;
}

.muted-action {
  color: $color-text-secondary;
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
