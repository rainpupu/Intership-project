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
      <StatisticCard label="待审核事件" :value="overview.stats.pendingEvents" hint="等待管理员确认" icon="📝" />
      <StatisticCard label="领养申请" :value="overview.stats.adoptionApplications" hint="待沟通与回访" icon="💌" />
    </section>

    <section class="dashboard-grid">
      <ChartCard
        title="领养申请趋势"
        description="当前为 Mock 示例数据，后续对接 dashboard 接口。"
        :labels="chartLabels"
        :values="chartValues"
      />

      <div class="soft-card panel">
        <h2 class="section-title">最近识别记录</h2>
        <div class="record-list">
          <article v-for="record in overview.recentRecognitions" :key="record.id">
            <img :src="record.image" :alt="record.catName" />
            <div>
              <strong>{{ record.catName }}</strong>
              <p>{{ record.location }} · {{ formatDateTime(record.createdAt) }}</p>
            </div>
            <el-tag>{{ formatPercent(record.similarity) }}</el-tag>
          </article>
        </div>
      </div>
    </section>

    <section class="soft-card panel">
      <h2 class="section-title">重点关注猫咪</h2>
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
import ChartCard from '@/components/dashboard/ChartCard.vue';
import StatisticCard from '@/components/dashboard/StatisticCard.vue';
import { formatDateTime, formatPercent } from '@/utils/formatter';

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
  adoptionTrend: [],
});
const loading = ref(false);
const errorMessage = ref('');

const chartLabels = computed(() => overview.adoptionTrend.map((item) => item.date));
const chartValues = computed(() => overview.adoptionTrend.map((item) => item.value));

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
