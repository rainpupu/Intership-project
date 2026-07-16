<template>
  <PageContainer>
    <DataState v-if="loading" type="loading" :rows="8" />
    <DataState v-else-if="errorMessage" type="error" :description="errorMessage" action-text="重新加载" @retry="fetchDetail" />
    <template v-else-if="cat">
      <RouterLink to="/cats" class="back-link">← 返回猫咪图鉴</RouterLink>

      <section class="detail-grid">
        <div class="media-card soft-card">
          <img class="cover" :src="activeImage" :alt="cat.name" />
          <div class="thumbs">
            <button
              v-for="image in cat.galleryImages"
              :key="image"
              class="thumb"
              :class="{ active: image === activeImage }"
              type="button"
              @click="activeImage = image"
            >
              <img :src="image" :alt="cat.name" />
            </button>
          </div>
        </div>

        <div class="info-card soft-card">
          <div class="title-row">
            <div>
              <h1>{{ cat.name }}</h1>
              <p>{{ cat.code }}</p>
            </div>
            <el-tag size="large">{{ cat.adoptionStatus }}</el-tag>
          </div>

          <p class="description">{{ cat.description }}</p>

          <dl class="basic-info">
            <div>
              <dt>毛色</dt>
              <dd>{{ cat.coatColor }}</dd>
            </div>
            <div>
              <dt>年龄阶段</dt>
              <dd>{{ cat.ageStage }}</dd>
            </div>
            <div>
              <dt>性别</dt>
              <dd>{{ cat.gender }}</dd>
            </div>
            <div>
              <dt>性格标签</dt>
              <dd>{{ cat.personalityTags.join(' / ') }}</dd>
            </div>
          </dl>

          <div class="actions">
            <el-button type="primary" size="large" round>申请领养</el-button>
            <el-button size="large" round>云领养</el-button>
          </div>
        </div>
      </section>

      <section class="status-grid">
        <CatStatusCard icon="💚" label="当前健康状态" :value="cat.healthStatus" hint="由最近观察记录生成" />
        <CatStatusCard icon="😊" label="当前情绪状态" :value="cat.moodStatus" hint="基于行为描述粗略判断" />
        <CatStatusCard icon="📍" label="最近出现地点" :value="cat.lastSeenLocation" />
        <CatStatusCard icon="🕒" label="最近出现时间" :value="formatDateTime(cat.lastSeenAt)" />
      </section>

      <section class="record-grid">
        <div class="soft-card panel">
          <h2 class="section-title">历史出现时间线</h2>
          <CatTimeline :observations="observations" />
        </div>
        <div class="soft-card panel ai-panel">
          <span>AI</span>
          <h2>综合评估</h2>
          <p>该档案已接入识别流程占位数据，后续可根据 FastAPI 返回的健康评分、地点热力和行为趋势继续扩展。</p>
        </div>
      </section>
    </template>

    <EmptyState v-else title="没有找到这只猫咪" description="请返回猫咪图鉴选择一个已有档案。" />
  </PageContainer>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { getCatDetail, getCatObservations } from '@/api/cat';
import CatStatusCard from '@/components/cat/CatStatusCard.vue';
import CatTimeline from '@/components/cat/CatTimeline.vue';
import DataState from '@/components/common/DataState.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import PageContainer from '@/components/common/PageContainer.vue';
import type { Cat, Observation } from '@/types/cat';
import { formatDateTime } from '@/utils/formatter';

const route = useRoute();
const cat = ref<Cat>();
const observations = ref<Observation[]>([]);
const activeImage = ref('');
const loading = ref(false);
const errorMessage = ref('');

async function fetchDetail() {
  const id = String(route.params.id);
  loading.value = true;
  errorMessage.value = '';
  try {
    cat.value = await getCatDetail(id);
    observations.value = await getCatObservations(id);
    activeImage.value = cat.value?.coverImage || '';
  } catch {
    errorMessage.value = '猫咪详情加载失败，请稍后重试。';
  } finally {
    loading.value = false;
  }
}

onMounted(fetchDetail);
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.back-link {
  display: inline-flex;
  margin-bottom: 18px;
  color: $color-primary-dark;
  font-weight: 800;
}

.detail-grid {
  display: grid;
  grid-template-columns: minmax(340px, 0.95fr) minmax(0, 1.05fr);
  gap: 22px;
}

.media-card,
.info-card,
.panel {
  padding: 18px;
}

.cover {
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: 22px;
  object-fit: cover;
}

.thumbs {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-top: 12px;
}

.thumb {
  padding: 0;
  overflow: hidden;
  border: 2px solid transparent;
  border-radius: 14px;
  background: transparent;
  cursor: pointer;

  &.active {
    border-color: $color-primary;
  }
}

.thumb img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
}

.title-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

h1 {
  margin: 0;
  color: $color-text;
  font-size: 36px;
}

.title-row p,
.description {
  color: $color-text-secondary;
}

.description {
  line-height: 1.8;
}

.basic-info {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin: 22px 0;
}

.basic-info div {
  padding: 14px;
  border-radius: 16px;
  background: rgba(255, 247, 237, 0.76);
}

dt {
  color: $color-text-secondary;
  font-size: 12px;
}

dd {
  margin: 5px 0 0;
  color: $color-text;
  font-weight: 800;
}

.actions {
  display: flex;
  gap: 12px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin: 22px 0;
}

.record-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(280px, 0.7fr);
  gap: 22px;
}

.ai-panel {
  min-height: 260px;
  background:
    radial-gradient(circle at 80% 15%, rgba(96, 165, 250, 0.22), transparent 32%),
    rgba(255, 255, 255, 0.82);
}

.ai-panel span {
  display: grid;
  width: 58px;
  height: 58px;
  place-items: center;
  border-radius: 22px;
  background: rgba(96, 165, 250, 0.2);
  color: #2563eb;
  font-weight: 900;
}

.ai-panel h2 {
  color: $color-text;
}

.ai-panel p {
  color: $color-text-secondary;
  line-height: 1.8;
}

@media (max-width: 980px) {
  .detail-grid,
  .record-grid {
    grid-template-columns: 1fr;
  }

  .status-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 620px) {
  .basic-info,
  .status-grid {
    grid-template-columns: 1fr;
  }
}
</style>
