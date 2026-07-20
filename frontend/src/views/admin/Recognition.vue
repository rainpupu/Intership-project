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
        <div class="upload-head">
          <div>
            <h2 class="section-title">多图片上传</h2>
            <p>上传后调用本地 YOLO 模型识别，并保存到当前管理员账号的识别历史。</p>
          </div>
          <el-button type="primary" round :loading="analyzing" @click="handleAnalyze">开始识别</el-button>
        </div>
        <UploadPanel @change="handleUploadChange" />
      </div>

      <div class="soft-card panel">
        <h2 class="section-title">最高置信度结果</h2>
        <div v-if="candidates.length" class="candidate-list">
          <CandidateCard v-for="candidate in candidates" :key="candidate.catId" :candidate="candidate" />
        </div>
        <EmptyState
          v-else
          title="暂无候选结果"
          description="上传图片并点击开始识别后，候选猫咪会显示在这里。"
        />
      </div>

      <div class="soft-card panel ai-report">
        <h2 class="section-title">AI 分析结果</h2>
        <p>{{ analysis.summary }}</p>
        <div v-if="createdCatInfo" class="identity-result created">
          <div>
            <span class="result-label">已创建新猫档案</span>
            <strong>{{ createdCatInfo.name || createdCatInfo.catId }}</strong>
            <p>系统已登记本次个体识别特征，并同步写入健康状态、心情状态和最近出现时间；地点仍由管理员人工补充。</p>
          </div>
          <el-button type="primary" round @click="fetchCats">刷新猫咪档案</el-button>
        </div>
        <div v-else-if="topCandidate" class="identity-result" :class="topCandidate.modelType">
          <img :src="topCandidate.cropImage || topCandidate.image" :alt="topCandidate.name" />
          <div class="result-content">
            <span class="result-label">{{ identityResultTitle }}</span>
            <strong>{{ identityResultName }}</strong>
            <p>{{ identityResultDescription }}</p>
            <div v-if="topCandidate.bestIdentityMatch" class="match-hint">
              最接近已有档案：{{ topCandidate.bestIdentityMatch.name }}，相似度
              {{ formatPercent(topCandidate.bestIdentityMatch.similarity) }}
            </div>
            <div class="result-actions">
              <el-button
                v-if="topCandidate.modelType === 'individual'"
                type="primary"
                round
                @click="confirmMatchedCandidate"
              >
                登记到匹配档案
              </el-button>
              <el-button
                v-if="topCandidate.modelType === 'new'"
                type="primary"
                round
                :loading="creatingCat"
                @click="handleDirectCreateNewCat"
              >
                直接创建档案
              </el-button>
              <el-button v-if="topCandidate.modelType === 'new'" round @click="createNew">编辑后创建</el-button>
            </div>
          </div>
        </div>
        <div v-else class="identity-result empty">
          <div>
            <span class="result-label">等待识别结果</span>
            <strong>尚未上传并识别图片</strong>
            <p>上传照片并点击开始识别后，这里会显示已有猫匹配结果；如果判断为新猫，可直接创建待完善档案。</p>
          </div>
        </div>
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
          <el-select
            v-model="selectedCatId"
            filterable
            clearable
            placeholder="选择已有猫咪档案"
            style="width: 220px"
          >
            <el-option v-for="cat in cats" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
          <el-button type="primary" round @click="confirmExisting">确认为已有猫</el-button>
          <el-button round @click="createNew">创建新猫档案</el-button>
          <el-button round @click="activeStep = 2">暂不确认</el-button>
        </div>
      </div>
    </section>

    <el-dialog v-model="createDialogVisible" title="创建新猫档案" width="520px">
      <div v-if="topCandidate" class="prefill-card">
        <img :src="topCandidate.cropImage || topCandidate.image" :alt="topCandidate.name" />
        <div>
          <strong>AI 已预填基础信息</strong>
            <p>候选类型：{{ topCandidate.modelType === 'new' ? '疑似新猫' : topCandidate.status }}</p>
            <p>品种/外观候选：{{ topCandidate.breedName || topCandidate.name }}</p>
            <p>健康状态：{{ topCandidate.healthStatus || '待人工确认' }}</p>
            <p>心情状态：{{ topCandidate.moodStatus || '待人工确认' }}</p>
            <p>置信度：{{ formatPercent(topCandidate.similarity) }}</p>
        </div>
      </div>
      <el-form label-width="92px">
        <el-form-item label="档案名称">
          <el-input v-model="newCatForm.name" placeholder="可直接使用系统生成名称，后续再补充昵称" />
        </el-form-item>
        <el-form-item label="猫咪编号">
          <el-input v-model="newCatForm.code" placeholder="留空则自动生成" />
        </el-form-item>
        <el-form-item label="发现地点">
          <el-input v-model="newCatForm.lastSeenLocation" placeholder="请人工输入，例如：东门、图书馆附近" />
        </el-form-item>
        <el-form-item label="档案备注">
          <el-input
            v-model="newCatForm.description"
            type="textarea"
            :rows="3"
            placeholder="由本次识别创建，可后续在猫咪管理中补全"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creatingCat" @click="handleCreateNewCat">确认创建</el-button>
      </template>
    </el-dialog>

    <section class="soft-card records-card">
      <div class="records-head">
        <div>
          <h2 class="section-title">全平台最近识别记录</h2>
          <p>管理员通过 `getRecognitionRecords({ scope: 'all' })` 查看所有用户上传记录。</p>
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
        @retry="fetchRecords"
      />
      <el-table v-else :data="records" row-key="id">
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
        <el-table-column prop="healthStatus" label="健康" width="110" />
        <el-table-column prop="moodStatus" label="心情" width="110" />
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
import { ElMessage } from 'element-plus';
import { getCatList } from '@/api/cat';
import { confirmExistingCat, getRecognitionRecords } from '@/api/recognition';
import CandidateCard from '@/components/recognition/CandidateCard.vue';
import DataState from '@/components/common/DataState.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import UploadPanel from '@/components/recognition/UploadPanel.vue';
import { useRecognitionFlow } from '@/composables/useRecognitionFlow';
import type { Cat } from '@/types/cat';
import type { RecognitionRecord } from '@/types/recognition';
import { formatDateTime, formatPercent } from '@/utils/formatter';

const records = ref<RecognitionRecord[]>([]);
const cats = ref<Cat[]>([]);
const selectedCatId = ref('');
const createDialogVisible = ref(false);
const creatingCat = ref(false);
const createdCatInfo = ref<{ catId: string; name?: string } | null>(null);
const newCatForm = reactive({
  name: '',
  code: '',
  lastSeenLocation: '',
  description: '',
});
const recordsLoading = ref(false);
const recordsError = ref('');
const {
  activeStep,
  analysis,
  analyzing,
  candidates,
  analyzeSelectedImages,
  createNewCatProfile,
  handleUploadChange,
} = useRecognitionFlow();

const topCandidate = computed(() => candidates.value[0]);
const identityResultTitle = computed(() => {
  if (!topCandidate.value) return '等待识别结果';
  if (topCandidate.value.modelType === 'individual') return '已匹配已有猫咪档案';
  if (topCandidate.value.modelType === 'new') return '疑似新猫，可创建档案';
  return '仅完成 YOLO 识别';
});
const identityResultName = computed(() => {
  if (!topCandidate.value) return '';
  if (topCandidate.value.modelType === 'new') return '系统将创建待完善新猫档案';
  return topCandidate.value.name;
});
const identityResultDescription = computed(() => {
  const candidate = topCandidate.value;
  if (!candidate) return '';
  if (candidate.modelType === 'individual') {
    return `个体识别模型匹配到已有档案「${candidate.name}」，相似度 ${formatPercent(candidate.similarity)}。`;
  }
  if (candidate.modelType === 'new') {
    const breedName = candidate.breedName || candidate.name || '未知品种';
    return `YOLO 检测到猫咪目标，个体识别未达到已有档案阈值。系统会用 ${breedName}、本次裁剪图、特征向量、健康状态和心情状态创建新档案。`;
  }
  return `${candidate.status}。如果这里没有个体匹配结果，请先确认个体识别模型文件存在，并且已有猫档案已登记参考特征。`;
});

async function confirmExisting() {
  if (!candidates.value.length) {
    ElMessage.warning('请先上传图片并完成识别');
    return;
  }
  if (!selectedCatId.value) {
    ElMessage.warning('请先选择要绑定的猫咪档案');
    return;
  }

  await confirmExistingCat(selectedCatId.value);
  activeStep.value = 4;
  ElMessage.success('已将本次识别特征登记到猫咪档案');
  await fetchRecords();
}

async function confirmMatchedCandidate() {
  const candidate = topCandidate.value;
  if (!candidate || candidate.modelType !== 'individual') {
    ElMessage.warning('当前没有可登记的已有猫匹配结果');
    return;
  }

  await confirmExistingCat(candidate.catId);
  activeStep.value = 4;
  ElMessage.success(`已登记到「${candidate.name}」档案`);
  await fetchRecords();
}

async function createNew() {
  if (!candidates.value.length) {
    ElMessage.warning('请先上传图片并完成识别');
    return;
  }
  fillNewCatFormFromCandidate();
  createDialogVisible.value = true;
}

function fillNewCatFormFromCandidate() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  const hour = String(now.getHours()).padStart(2, '0');
  const minute = String(now.getMinutes()).padStart(2, '0');
  const candidate = topCandidate.value;
  const breedName = candidate?.breedName || candidate?.name || '未知品种';
  newCatForm.name = `待命名猫咪-${month}${day}${hour}${minute}`;
  newCatForm.code = '';
  newCatForm.lastSeenLocation = '';
  const health = candidate?.healthStatus ? `；健康状态：${candidate.healthStatus}` : '';
  const mood = candidate?.moodStatus ? `；心情状态：${candidate.moodStatus}` : '';
  newCatForm.description = `由本次识别自动创建。AI 品种/外观候选：${breedName}；候选置信度：${candidate ? formatPercent(candidate.similarity) : '未知'}${health}${mood}。地点需要管理员人工补充。`;
}

async function handleCreateNewCat() {
  creatingCat.value = true;
  try {
    const result = await createNewCatProfile({
      name: newCatForm.name.trim(),
      code: newCatForm.code.trim() || undefined,
      lastSeenLocation: newCatForm.lastSeenLocation.trim() || undefined,
      description: newCatForm.description.trim() || undefined,
    });
    createdCatInfo.value = result;
    createDialogVisible.value = false;
    ElMessage.success('新猫档案已创建，并已登记本次识别特征');
    await Promise.all([fetchRecords(), fetchCats()]);
  } finally {
    creatingCat.value = false;
  }
}

async function handleDirectCreateNewCat() {
  if (!topCandidate.value || topCandidate.value.modelType !== 'new') {
    ElMessage.warning('当前结果不是疑似新猫，不能直接创建新档案');
    return;
  }

  fillNewCatFormFromCandidate();
  await handleCreateNewCat();
}

async function handleAnalyze() {
  createdCatInfo.value = null;
  const success = await analyzeSelectedImages();
  if (success) {
    await fetchRecords();
  }
}

onMounted(async () => {
  await Promise.all([fetchRecords(), fetchCats()]);
});

async function fetchCats() {
  cats.value = await getCatList();
}

async function fetchRecords() {
  recordsLoading.value = true;
  recordsError.value = '';
  try {
    records.value = await getRecognitionRecords({ scope: 'all' });
  } catch {
    recordsError.value = '全平台识别记录加载失败，请稍后重试。';
  } finally {
    recordsLoading.value = false;
  }
}
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

.candidate-list {
  display: grid;
  gap: 12px;
}

.upload-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 14px;
}

.upload-head p {
  margin: -8px 0 0;
  color: $color-text-secondary;
  line-height: 1.6;
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

.identity-result {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr);
  gap: 14px;
  align-items: center;
  margin: 16px 0;
  padding: 14px;
  border: 1px solid rgba(251, 146, 60, 0.18);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.76);
}

.identity-result.individual {
  border-color: rgba(34, 197, 94, 0.24);
  background: rgba(240, 253, 244, 0.72);
}

.identity-result.new {
  border-color: rgba(251, 146, 60, 0.28);
  background: rgba(255, 247, 237, 0.78);
}

.identity-result.created {
  grid-template-columns: minmax(0, 1fr) auto;
  border-color: rgba(34, 197, 94, 0.28);
  background: rgba(240, 253, 244, 0.74);
}

.identity-result.empty {
  display: block;
}

.identity-result img {
  width: 112px;
  height: 88px;
  border-radius: 10px;
  object-fit: cover;
  background: rgba(255, 247, 237, 0.78);
}

.result-content {
  min-width: 0;
}

.result-label {
  display: block;
  margin-bottom: 4px;
  color: $color-primary-dark;
  font-size: 12px;
  font-weight: 700;
}

.identity-result strong {
  display: block;
  font-size: 18px;
}

.identity-result p {
  margin: 6px 0 0;
}

.match-hint {
  margin-top: 8px;
  color: $color-text-secondary;
  font-size: 13px;
}

.result-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
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

.prefill-card {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr);
  gap: 14px;
  align-items: center;
  margin-bottom: 18px;
  padding: 12px;
  border: 1px solid rgba(251, 146, 60, 0.18);
  border-radius: 12px;
  background: rgba(255, 247, 237, 0.72);
}

.prefill-card img {
  width: 112px;
  height: 88px;
  border-radius: 10px;
  object-fit: cover;
}

.prefill-card p {
  margin: 4px 0 0;
  color: $color-text-secondary;
  font-size: 13px;
}

.record-image {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  object-fit: cover;
}

@media (max-width: 1100px) {
  .hint-grid {
    grid-template-columns: 1fr;
  }
}
</style>
