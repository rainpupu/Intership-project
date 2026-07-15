<template>
  <main class="admin-page">
    <section class="page-head">
      <div>
        <h1 class="page-title">猫咪管理</h1>
        <p class="page-subtitle">当前阶段提供列表骨架，后续可扩展新增档案、审核记录、批量标记等功能。</p>
      </div>
      <el-button type="primary" round>新增猫咪档案</el-button>
    </section>

    <section class="soft-card table-card">
      <el-table :data="cats" row-key="id">
        <el-table-column label="猫咪" min-width="220">
          <template #default="{ row }">
            <div class="cat-cell">
              <img :src="row.coverImage" :alt="row.name" />
              <div>
                <strong>{{ row.name }}</strong>
                <p>{{ row.code }}</p>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="coatColor" label="毛色" width="110" />
        <el-table-column prop="ageStage" label="年龄阶段" width="110" />
        <el-table-column prop="healthStatus" label="健康状态" width="130" />
        <el-table-column prop="adoptionStatus" label="领养状态" width="130" />
        <el-table-column prop="lastSeenLocation" label="最近出现地点" min-width="180" />
      </el-table>
    </section>
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { getCatList } from '@/api/cat';
import type { Cat } from '@/types/cat';

const cats = ref<Cat[]>([]);

onMounted(async () => {
  cats.value = await getCatList();
});
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.admin-page {
  padding: 28px;
}

.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
}

.table-card {
  overflow: hidden;
  padding: 8px;
}

.cat-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

img {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  object-fit: cover;
}

strong {
  color: $color-text;
}

p {
  margin: 4px 0 0;
  color: $color-text-secondary;
  font-size: 12px;
}
</style>
