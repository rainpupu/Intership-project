<template>
  <main class="admin-page">
    <section class="page-head">
      <div>
        <h1 class="page-title">线索审核</h1>
        <p class="page-subtitle">只处理用户主动提交的校园猫线索。已有猫按个体识别结果绑定，新猫直接创建待完善档案。</p>
      </div>
      <el-button round :loading="loading" @click="fetchData">刷新</el-button>
    </section>

    <DataState v-if="loading" type="loading" :rows="5" />
    <DataState
      v-else-if="errorMessage"
      type="error"
      :description="errorMessage"
      action-text="重新加载"
      @retry="fetchData"
    />
    <section v-else class="soft-card panel">
      <EmptyState
        v-if="clues.length === 0"
        title="暂无待审核线索"
        description="用户在我的识别中提交校园线索后，会集中显示在这里。"
      />
      <el-table v-else :data="clues" row-key="id">
        <el-table-column label="图片" width="96">
          <template #default="{ row }">
            <img class="record-image" :src="row.image" :alt="row.catName" />
          </template>
        </el-table-column>
        <el-table-column label="模型判定" min-width="220">
          <template #default="{ row }">
            <div class="decision-cell">
              <el-tag :type="decisionTagType(row)" effect="light">{{ decisionTitle(row) }}</el-tag>
              <strong>{{ decisionName(row) }}</strong>
              <span>{{ decisionDescription(row) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="品种" min-width="130">
          <template #default="{ row }">{{ row.breedName || row.catName || '待确认' }}</template>
        </el-table-column>
        <el-table-column label="相似度" width="100">
          <template #default="{ row }">{{ formatPercent(row.similarity) }}</template>
        </el-table-column>
        <el-table-column prop="healthStatus" label="健康" width="110" />
        <el-table-column prop="moodStatus" label="心情" width="110" />
        <el-table-column prop="location" label="拍摄地点" min-width="170" />
        <el-table-column label="拍摄时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.observedAt || row.createdAt) }}</template>
        </el-table-column>
        <el-table-column prop="userRemark" label="用户备注" min-width="220" show-overflow-tooltip />
        <el-table-column label="审核操作" width="210" fixed="right">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button
                v-if="isExistingMatch(row)"
                link
                type="primary"
                :loading="actingRecordId === row.id"
                @click="confirmModelMatch(row)"
              >
                绑定模型匹配档案
              </el-button>
              <el-button
                v-else-if="isNewCat(row)"
                link
                type="primary"
                :loading="actingRecordId === row.id"
                @click="createCatFromClue(row)"
              >
                新建档案
              </el-button>
              <el-tooltip v-else content="该线索没有可登记的个体特征，需要重新识别或忽略">
                <el-tag type="warning" effect="plain">无法自动入库</el-tag>
              </el-tooltip>
              <el-popconfirm title="确定忽略这条线索吗？" @confirm="dismiss(row)">
                <template #reference>
                  <el-button link type="danger" :loading="actingRecordId === row.id">忽略</el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import {
  confirmExistingCatForRecord,
  createNewCatFromRecord,
  dismissCampusClue,
  getRecognitionRecords,
} from '@/api/recognition';
import DataState from '@/components/common/DataState.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import type { RecognitionRecord } from '@/types/recognition';
import { formatDateTime, formatPercent } from '@/utils/formatter';

const clues = ref<RecognitionRecord[]>([]);
const loading = ref(false);
const errorMessage = ref('');
const actingRecordId = ref('');

async function fetchData() {
  loading.value = true;
  errorMessage.value = '';
  try {
    clues.value = await getRecognitionRecords({ scope: 'clues' });
  } catch {
    errorMessage.value = '线索审核列表加载失败，请稍后重试。';
  } finally {
    loading.value = false;
  }
}

function isBreedPlaceholder(catId?: string | null) {
  return !catId || catId.startsWith('breed-');
}

function isExistingMatch(record: RecognitionRecord) {
  return !isBreedPlaceholder(record.catId) && record.modelType !== 'new';
}

function isNewCat(record: RecognitionRecord) {
  return record.modelType === 'new';
}

function decisionTagType(record: RecognitionRecord) {
  if (isExistingMatch(record)) return 'success';
  if (isNewCat(record)) return 'warning';
  return 'info';
}

function decisionTitle(record: RecognitionRecord) {
  if (isExistingMatch(record)) return '已有猫匹配';
  if (isNewCat(record)) return '疑似新猫';
  return '待人工复查';
}

function decisionName(record: RecognitionRecord) {
  if (isExistingMatch(record)) return record.catName;
  return record.breedName || record.catName || '未命名新猫';
}

function decisionDescription(record: RecognitionRecord) {
  if (isExistingMatch(record)) {
    return `个体模型匹配到 ${record.catName}，确认后补充本次地点、健康和心情记录。`;
  }
  if (record.bestIdentityMatch) {
    return `低于入库阈值，最接近 ${record.bestIdentityMatch.name} ${formatPercent(record.bestIdentityMatch.similarity)}。`;
  }
  if (record.identityStatus) return record.identityStatus;
  return '未匹配到已有档案，确认后将创建新猫档案。';
}

async function confirmModelMatch(record: RecognitionRecord) {
  if (!isExistingMatch(record) || !record.catId) {
    ElMessage.warning('该线索没有模型匹配到的已有猫档案');
    return;
  }

  actingRecordId.value = record.id;
  try {
    await confirmExistingCatForRecord(record.id, record.catId);
    ElMessage.success(`已绑定到 ${record.catName} 档案`);
    notifyPendingCountChanged();
    await fetchData();
  } finally {
    actingRecordId.value = '';
  }
}

async function createCatFromClue(record: RecognitionRecord) {
  if (!isNewCat(record)) {
    ElMessage.warning('该线索已匹配已有档案，不应新建档案');
    return;
  }

  actingRecordId.value = record.id;
  try {
    const result = await createNewCatFromRecord(record.id, {
      lastSeenLocation: record.location,
      description: buildAutoDescription(record),
    });
    ElMessage.success(`已创建新猫档案：${result.name || result.catId}`);
    notifyPendingCountChanged();
    await fetchData();
  } finally {
    actingRecordId.value = '';
  }
}

async function dismiss(record: RecognitionRecord) {
  actingRecordId.value = record.id;
  try {
    await dismissCampusClue(record.id);
    ElMessage.success('已忽略该线索');
    notifyPendingCountChanged();
    await fetchData();
  } finally {
    actingRecordId.value = '';
  }
}

function buildAutoDescription(record: RecognitionRecord) {
  const parts = [
    '由用户提交的校园猫线索自动创建。',
    `AI 品种候选：${record.breedName || record.catName || '未知品种'}。`,
    `候选置信度：${formatPercent(record.similarity)}。`,
  ];
  if (record.healthStatus) parts.push(`健康状态：${record.healthStatus}。`);
  if (record.moodStatus) parts.push(`心情状态：${record.moodStatus}。`);
  if (record.userRemark) parts.push(`用户备注：${record.userRemark}。`);
  return parts.join('');
}

function notifyPendingCountChanged() {
  window.dispatchEvent(new Event('cattrace:pending-clues-updated'));
}

onMounted(fetchData);
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.admin-page {
  padding: 28px;
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 22px;
}

.panel {
  padding: 20px;
  overflow: hidden;
}

.record-image {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  object-fit: cover;
}

.decision-cell {
  display: grid;
  gap: 5px;
}

.decision-cell strong {
  color: $color-text;
}

.decision-cell span:last-child {
  color: $color-text-secondary;
  font-size: 13px;
  line-height: 1.5;
}

.table-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

@media (max-width: 720px) {
  .page-head {
    flex-direction: column;
  }
}
</style>
