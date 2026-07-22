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
            <el-button size="large" round @click="openCloudAdoption">云领养</el-button>
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
          <p>系统会结合最近观察记录、识别结果和管理员标记，持续更新健康状态、活动地点和行为趋势。</p>
        </div>
      </section>
    </template>

    <EmptyState v-else title="没有找到这只猫咪" description="请返回猫咪图鉴选择一个已有档案。" />

    <el-dialog
      v-model="cloudDialogVisible"
      class="cloud-adoption-dialog"
      width="min(860px, 94vw)"
      :title="cat ? `云领养支持 · ${cat.name}` : '云领养支持'"
    >
      <div v-if="cat" class="cloud-adoption">
        <section class="support-hero">
          <img :src="cat.coverImage" :alt="cat.name" />
          <div>
            <span class="support-label">云支持对象</span>
            <h2>{{ cat.name }}</h2>
            <p>选择一份物资支持，平台将记录为该猫咪的云领养关怀。物资会用于日常投喂、环境改善或健康维护。</p>
          </div>
        </section>

        <el-radio-group v-model="activeGiftCategory" class="category-tabs" size="large">
          <el-radio-button label="food">食物</el-radio-button>
          <el-radio-button label="toy">玩具</el-radio-button>
          <el-radio-button label="health">健康</el-radio-button>
        </el-radio-group>

        <section class="gift-grid">
          <button
            v-for="gift in filteredGiftItems"
            :key="gift.id"
            class="gift-card"
            :class="{ active: gift.id === selectedGiftId }"
            type="button"
            @click="selectedGiftId = gift.id"
          >
            <span class="gift-icon">{{ gift.icon }}</span>
            <strong>{{ gift.name }}</strong>
            <small>{{ gift.description }}</small>
            <em>¥{{ gift.price }}</em>
          </button>
        </section>

        <section class="purchase-panel">
          <div class="quantity-row">
            <span>支持数量</span>
            <el-input-number v-model="quantity" :min="1" :max="99" />
          </div>
          <div class="payment-row">
            <span>支付方式</span>
            <el-radio-group v-model="paymentMethod">
              <el-radio label="微信支付">微信支付</el-radio>
              <el-radio label="支付宝">支付宝</el-radio>
              <el-radio label="校园卡">校园卡</el-radio>
            </el-radio-group>
          </div>
          <div class="summary-row">
            <div>
              <span>本次支持</span>
              <strong>{{ supportSummary }}</strong>
            </div>
            <div class="total-price">¥{{ totalAmount }}</div>
          </div>
        </section>
      </div>
      <template #footer>
        <el-button round @click="cloudDialogVisible = false">取消</el-button>
        <el-button type="primary" round :disabled="!selectedGift" :loading="submittingOrder" @click="confirmCloudAdoption">
          确认支持
        </el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { createCloudAdoptionOrder } from '@/api/cloudAdoption';
import { getCatDetail, getCatObservations } from '@/api/cat';
import { getRequestErrorMessage } from '@/api/request';
import CatStatusCard from '@/components/cat/CatStatusCard.vue';
import CatTimeline from '@/components/cat/CatTimeline.vue';
import DataState from '@/components/common/DataState.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import PageContainer from '@/components/common/PageContainer.vue';
import type { Cat, Observation } from '@/types/cat';
import type { CloudGiftCategory } from '@/types/cloudAdoption';
import { formatDateTime } from '@/utils/formatter';

const route = useRoute();
const cat = ref<Cat>();
const observations = ref<Observation[]>([]);
const activeImage = ref('');
const loading = ref(false);
const errorMessage = ref('');
const cloudDialogVisible = ref(false);
const activeGiftCategory = ref<'food' | 'toy' | 'health'>('food');
const selectedGiftId = ref('food-kibble');
const quantity = ref(1);
const paymentMethod = ref('微信支付');
const submittingOrder = ref(false);

interface CloudGiftItem {
  id: string;
  category: CloudGiftCategory;
  icon: string;
  name: string;
  description: string;
  price: number;
}

const giftItems: CloudGiftItem[] = [
  { id: 'food-kibble', category: 'food', icon: '🥣', name: '猫粮补给', description: '用于一次日常干粮投喂', price: 6 },
  { id: 'food-can', category: 'food', icon: '🥫', name: '湿粮罐头', description: '补充水分和蛋白质摄入', price: 12 },
  { id: 'food-week', category: 'food', icon: '📦', name: '一周口粮', description: '支持固定投喂点一周口粮', price: 38 },
  { id: 'toy-wand', category: 'toy', icon: '🎣', name: '逗猫棒', description: '丰富互动和运动时间', price: 9 },
  { id: 'toy-scratch', category: 'toy', icon: '🧶', name: '抓板玩具', description: '减少压力并满足抓挠需求', price: 18 },
  { id: 'toy-bed', category: 'toy', icon: '🛏️', name: '保暖猫窝', description: '改善休息和避寒环境', price: 32 },
  { id: 'health-deworm', category: 'health', icon: '🛡️', name: '驱虫支持', description: '支持基础体内外驱虫', price: 28 },
  { id: 'health-kit', category: 'health', icon: '🧰', name: '基础药箱', description: '补充碘伏、纱布等护理用品', price: 45 },
  { id: 'health-check', category: 'health', icon: '🩺', name: '健康复查', description: '支持一次基础健康观察复查', price: 68 },
];

const filteredGiftItems = computed(() => giftItems.filter((gift) => gift.category === activeGiftCategory.value));
const selectedGift = computed(() => giftItems.find((gift) => gift.id === selectedGiftId.value));
const totalAmount = computed(() => (selectedGift.value ? selectedGift.value.price * quantity.value : 0));
const supportSummary = computed(() => {
  if (!selectedGift.value) return '请选择支持物资';
  return `${selectedGift.value.name} × ${quantity.value}`;
});

function openCloudAdoption() {
  cloudDialogVisible.value = true;
}

async function confirmCloudAdoption() {
  if (!cat.value || !selectedGift.value) return;
  submittingOrder.value = true;
  try {
    await createCloudAdoptionOrder({
      catId: cat.value.id,
      giftId: selectedGift.value.id,
      giftCategory: selectedGift.value.category,
      giftName: selectedGift.value.name,
      giftDescription: selectedGift.value.description,
      giftIcon: selectedGift.value.icon,
      quantity: quantity.value,
      unitPrice: selectedGift.value.price,
      paymentMethod: paymentMethod.value,
    });
    ElMessage.success(`已为「${cat.value.name}」送出 ${supportSummary.value}，管理员可在云领养订单中查看。`);
    cloudDialogVisible.value = false;
  } catch (error) {
    ElMessage.error(getRequestErrorMessage(error, '云领养订单提交失败'));
  } finally {
    submittingOrder.value = false;
  }
}

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
  flex-wrap: wrap;
  gap: 12px;
}

.cloud-adoption {
  display: grid;
  gap: 18px;
}

.support-hero {
  display: grid;
  grid-template-columns: 104px minmax(0, 1fr);
  gap: 16px;
  align-items: center;
  padding: 14px;
  border: 1px solid rgba(251, 146, 60, 0.18);
  border-radius: 14px;
  background: rgba(255, 247, 237, 0.72);
}

.support-hero img {
  width: 104px;
  height: 104px;
  border-radius: 12px;
  object-fit: cover;
}

.support-label {
  color: $color-primary-dark;
  font-size: 12px;
  font-weight: 800;
}

.support-hero h2 {
  margin: 4px 0 6px;
  color: $color-text;
  font-size: 24px;
}

.support-hero p {
  margin: 0;
  color: $color-text-secondary;
  line-height: 1.7;
}

.category-tabs {
  width: fit-content;
}

.gift-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.gift-card {
  display: grid;
  min-height: 168px;
  gap: 8px;
  padding: 14px;
  border: 1px solid rgba(251, 146, 60, 0.18);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.78);
  color: $color-text;
  cursor: pointer;
  text-align: left;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.gift-card:hover,
.gift-card.active {
  border-color: rgba(251, 146, 60, 0.55);
  box-shadow: 0 12px 26px rgba(180, 104, 48, 0.12);
  transform: translateY(-1px);
}

.gift-icon {
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  border-radius: 14px;
  background: rgba(251, 146, 60, 0.12);
  font-size: 24px;
}

.gift-card strong {
  font-size: 16px;
}

.gift-card small {
  color: $color-text-secondary;
  line-height: 1.5;
}

.gift-card em {
  color: $color-primary-dark;
  font-size: 18px;
  font-style: normal;
  font-weight: 900;
}

.purchase-panel {
  display: grid;
  gap: 14px;
  padding: 16px;
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.9);
}

.quantity-row,
.payment-row,
.summary-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.quantity-row > span,
.payment-row > span,
.summary-row span {
  color: $color-text-secondary;
  font-weight: 700;
}

.summary-row {
  padding-top: 12px;
  border-top: 1px solid rgba(148, 163, 184, 0.22);
}

.summary-row strong {
  display: block;
  margin-top: 4px;
  color: $color-text;
  font-size: 17px;
}

.total-price {
  color: $color-primary-dark;
  font-size: 30px;
  font-weight: 900;
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

  .support-hero,
  .gift-grid {
    grid-template-columns: 1fr;
  }

  .quantity-row,
  .payment-row,
  .summary-row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
