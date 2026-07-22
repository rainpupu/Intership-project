<template>
  <main class="admin-page">
    <section class="page-head">
      <div>
        <h1 class="page-title">云领养订单</h1>
        <p class="page-subtitle">集中查看用户为猫咪购买的虚拟食物、玩具和健康支持记录。</p>
      </div>
      <el-button type="primary" round :loading="loading" @click="fetchOrders">刷新</el-button>
    </section>

    <section class="stats-grid">
      <div class="soft-card stat-card">
        <span>订单总数</span>
        <strong>{{ orders.length }}</strong>
      </div>
      <div class="soft-card stat-card">
        <span>支持金额</span>
        <strong>¥{{ totalAmount }}</strong>
      </div>
      <div class="soft-card stat-card">
        <span>支持物资</span>
        <strong>{{ totalQuantity }}</strong>
      </div>
    </section>

    <DataState v-if="loading" type="loading" :rows="8" />
    <DataState v-else-if="errorMessage" type="error" :description="errorMessage" action-text="重新加载" @retry="fetchOrders" />
    <section v-else class="soft-card order-panel">
      <EmptyState v-if="orders.length === 0" title="暂无云领养订单" description="用户在猫咪详情页完成云领养支持后，订单会显示在这里。" />
      <el-table v-else :data="orders" stripe>
        <el-table-column label="订单信息" min-width="190">
          <template #default="{ row }">
            <div class="order-no">{{ row.orderNo }}</div>
            <p>{{ formatDateTime(row.createdAt) }}</p>
          </template>
        </el-table-column>
        <el-table-column label="猫咪" min-width="180">
          <template #default="{ row }">
            <div class="cat-cell">
              <img :src="row.catCoverImage" :alt="row.catName" />
              <div>
                <strong>{{ row.catName }}</strong>
                <p>{{ row.catCode }}</p>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="supporterName" label="支持用户" min-width="130" />
        <el-table-column label="支持物资" min-width="190">
          <template #default="{ row }">
            <div class="gift-cell">
              <span>{{ row.giftIcon }}</span>
              <div>
                <strong>{{ row.giftName }} × {{ row.quantity }}</strong>
                <p>{{ row.giftDescription }}</p>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="paymentMethod" label="支付方式" width="120" />
        <el-table-column label="金额" width="110" align="right">
          <template #default="{ row }">
            <strong class="amount">¥{{ row.totalAmount }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag type="success">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { getCloudAdoptionOrders } from '@/api/cloudAdoption';
import { getRequestErrorMessage } from '@/api/request';
import DataState from '@/components/common/DataState.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import type { CloudAdoptionOrder } from '@/types/cloudAdoption';
import { formatDateTime } from '@/utils/formatter';

const orders = ref<CloudAdoptionOrder[]>([]);
const loading = ref(false);
const errorMessage = ref('');

const totalAmount = computed(() => orders.value.reduce((sum, order) => sum + order.totalAmount, 0));
const totalQuantity = computed(() => orders.value.reduce((sum, order) => sum + order.quantity, 0));

async function fetchOrders() {
  loading.value = true;
  errorMessage.value = '';
  try {
    orders.value = await getCloudAdoptionOrders();
  } catch (error) {
    errorMessage.value = getRequestErrorMessage(error, '云领养订单加载失败');
  } finally {
    loading.value = false;
  }
}

onMounted(fetchOrders);
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.admin-page {
  padding: 28px;
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 22px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 22px;
}

.stat-card {
  padding: 18px;
}

.stat-card span,
p {
  margin: 4px 0 0;
  color: $color-text-secondary;
  font-size: 13px;
}

.stat-card strong {
  display: block;
  margin-top: 8px;
  color: $color-text;
  font-size: 28px;
}

.order-panel {
  padding: 18px;
}

.order-no,
strong {
  color: $color-text;
  font-weight: 900;
}

.cat-cell,
.gift-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cat-cell img {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  object-fit: cover;
}

.gift-cell span {
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border-radius: 12px;
  background: rgba(251, 146, 60, 0.12);
  font-size: 22px;
}

.amount {
  color: $color-primary-dark;
}

@media (max-width: 760px) {
  .page-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
