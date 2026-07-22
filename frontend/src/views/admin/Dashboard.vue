<template>
  <main class="admin-page">
    <section class="page-head">
      <div>
        <h1 class="page-title">管理端首页</h1>
        <p class="page-subtitle">集中查看猫咪档案、识别任务、待处理事件和领养申请。</p>
      </div>
    </section>

    <DataState v-if="loading" type="loading" :rows="8" />
    <DataState v-else-if="errorMessage" type="error" :description="errorMessage" action-text="重新加载" @retry="fetchOverview" />
    <template v-else>
    <section class="stats-grid">
      <StatisticCard label="猫咪总数" :value="overview.stats.totalCats" hint="已建立数字档案" icon="🐾" />
      <StatisticCard label="今日识别" :value="overview.stats.todayRecognitions" hint="来自上传任务" icon="📷" />
      <StatisticCard label="待跟进事件" :value="overview.stats.pendingEvents" hint="重点关注或需复查" icon="📝" />
      <StatisticCard label="开放领养" :value="overview.stats.adoptionOpen" hint="状态为待领养" icon="💌" />
    </section>

    <section class="dashboard-grid">
      <ChartCard
        title="最近 7 天识别趋势"
        description="来自真实识别历史记录。"
        :labels="chartLabels"
        :values="chartValues"
      />

      <div class="soft-card panel">
        <h2 class="section-title">最近识别记录</h2>
        <EmptyState v-if="overview.recentRecognitions.length === 0" title="暂无识别记录" description="完成猫咪识别后，最近记录会显示在这里。" />
        <div class="record-list">
          <article v-for="record in overview.recentRecognitions" :key="record.id">
            <img :src="record.image" :alt="record.catName" />
            <div>
              <strong>{{ record.catName }}</strong>
              <p>{{ record.location }} · {{ formatDateTime(record.createdAt) }}</p>
            </div>
            <el-tag :type="recordMatchTagType(record)">
              {{ recordMatchStatusText(record) }}
            </el-tag>
          </article>
        </div>
      </div>
    </section>

    <section class="soft-card panel">
      <h2 class="section-title">重点关注猫咪</h2>
      <EmptyState v-if="overview.focusCats.length === 0" title="暂无重点关注猫咪" description="被标记、重点关注或需复查的猫咪会显示在这里。" />
      <div class="focus-list">
        <article v-for="cat in overview.focusCats" :key="cat.id">
          <img :src="cat.coverImage" :alt="cat.name" />
          <div>
            <strong>{{ cat.name }}</strong>
            <p>{{ cat.healthStatus }} · {{ cat.lastSeenLocation }}</p>
          </div>
          <el-tag type="warning">需跟进</el-tag>
        </article>
      </div>
    </section>
    </template>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { getDashboardOverview, type DashboardOverview } from '@/api/dashboard';
import DataState from '@/components/common/DataState.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import ChartCard from '@/components/dashboard/ChartCard.vue';
import StatisticCard from '@/components/dashboard/StatisticCard.vue';
import { formatDateTime } from '@/utils/formatter';

const overview = reactive<DashboardOverview>({
  stats: {
    totalCats: 0,
    todayRecognitions: 0,
    pendingEvents: 0,
    adoptionApplications: 0,
    adoptionOpen: 0,
    focusCats: 0,
  },
  recentRecognitions: [],
  focusCats: [],
  recognitionTrend: [],
});

function recordMatchStatusText(record: DashboardOverview['recentRecognitions'][number]) {
  if (record.modelType === 'individual' || (record.catId && !record.catId.startsWith('breed-'))) return '已匹配';
  if (record.modelType === 'new') return '未匹配';
  if (record.modelType === 'breed') return '仅识别品种';
  return '待确认';
}

function recordMatchTagType(record: DashboardOverview['recentRecognitions'][number]) {
  if (record.modelType === 'individual' || (record.catId && !record.catId.startsWith('breed-'))) return 'success';
  if (record.modelType === 'new') return 'warning';
  return 'info';
}
const loading = ref(false);
const errorMessage = ref('');

const chartLabels = computed(() => overview.recognitionTrend.map((item) => item.date));
const chartValues = computed(() => overview.recognitionTrend.map((item) => item.value));

async function fetchOverview() {
  loading.value = true;
  errorMessage.value = '';
  try {
    Object.assign(overview, await getDashboardOverview());
  } catch {
    errorMessage.value = '管理端概览加载失败，请稍后重试。';
  } finally {
    loading.value = false;
  }
}

onMounted(fetchOverview);
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.admin-page {
  padding: 28px;
}

.page-head {
  margin-bottom: 22px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 22px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(330px, 0.8fr);
  gap: 22px;
  margin-bottom: 22px;
}

.panel {
  padding: 20px;
}

.record-list,
.focus-list {
  display: grid;
  gap: 12px;
}

.record-list article,
.focus-list article {
  display: grid;
  grid-template-columns: 56px 1fr auto;
  gap: 12px;
  align-items: center;
  padding: 12px;
  border-radius: 16px;
  background: rgba(255, 247, 237, 0.72);
}

img {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  object-fit: cover;
}

strong {
  color: $color-text;
}

p {
  margin: 5px 0 0;
  color: $color-text-secondary;
  font-size: 13px;
}

@media (max-width: 1100px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 620px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
