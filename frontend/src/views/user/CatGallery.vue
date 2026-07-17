<template>
  <PageContainer>
    <section class="gallery-head">
      <div>
        <h1 class="page-title">猫咪图鉴</h1>
        <p class="page-subtitle">浏览已经入库的校园猫咪档案，查看领养状态、健康状态和最近出现位置。</p>
      </div>
      <el-input v-model="searchKeyword" class="search" placeholder="搜索名称、编号、毛色或地点" clearable />
    </section>

    <section class="filter-bar soft-card">
      <el-radio-group v-model="selectedFilter">
        <el-radio-button v-for="item in filters" :key="item" :label="item" />
      </el-radio-group>
    </section>

    <DataState v-if="loading" type="loading" :rows="8" />
    <DataState v-else-if="errorMessage" type="error" :description="errorMessage" action-text="重新加载" @retry="fetchCats" />
    <div v-else-if="filteredCats.length" class="cat-grid">
      <CatCard v-for="cat in filteredCats" :key="cat.id" :cat="cat" />
    </div>
    <EmptyState v-else title="暂无匹配猫咪" description="换一个筛选条件或搜索关键词试试。" />
  </PageContainer>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { getCatList } from '@/api/cat';
import CatCard from '@/components/cat/CatCard.vue';
import DataState from '@/components/common/DataState.vue';
import EmptyState from '@/components/common/EmptyState.vue';
import PageContainer from '@/components/common/PageContainer.vue';
import type { Cat } from '@/types/cat';

const route = useRoute();
const router = useRouter();
const filters = ['全部', '待领养', '已领养', '重点关注', '幼猫', '亲人'];

/** 从 URL query 参数读取初始筛选条件 */
const q = route.query.filter as string | undefined;
const selectedFilter = ref<string>(q && filters.includes(q) ? q : '全部');
const searchKeyword = ref('');
const cats = ref<Cat[]>([]);
const loading = ref(false);
const errorMessage = ref('');

const filteredCats = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();

  return cats.value.filter((cat) => {
    const matchFilter =
      selectedFilter.value === '全部' ||
      cat.adoptionStatus === selectedFilter.value ||
      (selectedFilter.value === '重点关注' && cat.isFocus) ||
      cat.ageStage === selectedFilter.value ||
      cat.personalityTags.includes(selectedFilter.value);

    const matchKeyword =
      !keyword ||
      [cat.name, cat.code, cat.coatColor, cat.lastSeenLocation].some((value) => value.toLowerCase().includes(keyword));

    return matchFilter && matchKeyword;
  });
});

async function fetchCats() {
  loading.value = true;
  errorMessage.value = '';
  try {
    cats.value = await getCatList();
  } catch {
    errorMessage.value = '猫咪图鉴加载失败，请检查网络或稍后重试。';
  } finally {
    loading.value = false;
  }
}

onMounted(fetchCats);

// 筛选条件变更时同步到 URL query 参数
watch(selectedFilter, (val) => {
  router.replace({ query: val === '全部' ? {} : { filter: val } });
});
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.gallery-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 22px;
}

.search {
  width: 320px;
}

.filter-bar {
  margin-bottom: 22px;
  padding: 16px;
}

.cat-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

@media (max-width: 980px) {
  .gallery-head {
    align-items: stretch;
    flex-direction: column;
  }

  .search {
    width: 100%;
  }

  .cat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 620px) {
  .cat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
