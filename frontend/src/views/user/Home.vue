<template>
  <PageContainer>
    <section class="hero">
      <div class="hero-copy">
        <el-tag effect="plain" size="large">AI 视觉识别 · 流浪猫数字档案</el-tag>
        <h1>给每一只流浪猫<br />一个<span>温暖的家</span></h1>
        <p>通过视觉识别与 AI 智能体，为流浪猫建立持续更新的数字档案。</p>
        <div class="hero-actions">
          <RouterLink to="/cats">
            <el-button type="primary" size="large" round>查看猫咪图鉴</el-button>
          </RouterLink>
          <RouterLink to="/admin/dashboard">
            <el-button size="large" round>进入管理端</el-button>
          </RouterLink>
          <RouterLink to="/chat">
            <el-button size="large" round>AI 助手</el-button>
          </RouterLink>
        </div>
      </div>
      <div class="hero-visual paw-dot">
        <img :src="featuredCat?.coverImage" alt="CatTrace 推荐猫咪" />
        <div class="robot-bubble">Hi，我是 AI 助手小橘</div>
      </div>
    </section>

    <section class="stats-grid">
      <StatisticCard label="已入库猫咪" :value="stats.totalCats" hint="持续更新数字档案" icon="🐾" />
      <StatisticCard label="待领养猫咪" :value="stats.adoptionOpen" hint="等待新的家" icon="💛" />
      <StatisticCard label="今日识别次数" :value="stats.todayRecognitions" hint="来自校园观测点" icon="📷" />
      <StatisticCard label="重点关注猫咪" :value="stats.focusCats" hint="需要健康或行为复查" icon="🩺" />
    </section>

    <section class="content-grid">
      <div>
        <h2 class="section-title">待领养精选</h2>
        <div class="cat-row">
          <CatCard v-for="cat in recommendedCats" :key="cat.id" :cat="cat" />
        </div>
      </div>

      <aside class="assistant-entry glass-card">
        <span>🤖</span>
        <h2>AI 助手入口</h2>
        <p>根据猫咪性格、健康状态和领养条件，为你推荐更合适的领养选择。</p>
        <RouterLink to="/chat">
          <el-button type="primary" round>开始咨询</el-button>
        </RouterLink>
      </aside>
    </section>
  </PageContainer>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { getCatList } from '@/api/cat';
import { getDashboardOverview } from '@/api/dashboard';
import CatCard from '@/components/cat/CatCard.vue';
import PageContainer from '@/components/common/PageContainer.vue';
import StatisticCard from '@/components/dashboard/StatisticCard.vue';
import type { Cat } from '@/types/cat';

const cats = ref<Cat[]>([]);
const stats = reactive({
  totalCats: 0,
  adoptionOpen: 0,
  todayRecognitions: 0,
  focusCats: 0,
});

const featuredCat = computed(() => cats.value[0]);
const recommendedCats = computed(() => cats.value.filter((cat) => cat.adoptionStatus === '待领养').slice(0, 3));

onMounted(async () => {
  cats.value = await getCatList();
  const overview = await getDashboardOverview();
  Object.assign(stats, overview.stats);
});
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;
@use '@/assets/styles/mixins' as *;

.hero {
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(360px, 1.05fr);
  gap: 28px;
  align-items: stretch;
  min-height: 430px;
  overflow: hidden;
  @include card-shell(30px);
}

.hero-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 54px 42px;
}

h1 {
  margin: 22px 0 16px;
  color: $color-text;
  font-size: clamp(38px, 5vw, 62px);
  line-height: 1.08;
  letter-spacing: 0;
}

h1 span {
  color: $color-primary-dark;
}

.hero-copy p {
  max-width: 560px;
  margin: 0;
  color: $color-text-secondary;
  font-size: 17px;
  line-height: 1.8;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 30px;
}

.hero-visual {
  position: relative;
  min-height: 430px;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.1), rgba(255, 247, 237, 0.76)),
    $color-primary-light;
}

.hero-visual img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.robot-bubble {
  position: absolute;
  right: 26px;
  bottom: 24px;
  padding: 14px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.88);
  color: $color-text;
  font-weight: 800;
  box-shadow: $shadow-soft;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin: 24px 0 34px;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 24px;
  align-items: start;
}

.cat-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.assistant-entry {
  padding: 26px;
  border-radius: 24px;
}

.assistant-entry span {
  font-size: 42px;
}

.assistant-entry h2 {
  margin: 12px 0 10px;
  color: $color-text;
}

.assistant-entry p {
  color: $color-text-secondary;
  line-height: 1.7;
}

@media (max-width: 980px) {
  .hero,
  .content-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid,
  .cat-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .stats-grid,
  .cat-row {
    grid-template-columns: 1fr;
  }

  .hero-copy {
    padding: 34px 24px;
  }
}
</style>
