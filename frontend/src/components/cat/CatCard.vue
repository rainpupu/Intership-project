<template>
  <RouterLink class="cat-card" :to="`/cats/${cat.id}`">
    <div class="cover">
      <img :src="cat.coverImage" :alt="cat.name" />
      <el-tag class="status" :type="statusType" effect="light">{{ cat.adoptionStatus }}</el-tag>
    </div>

    <div class="body">
      <div class="title-row">
        <h3>{{ cat.name }}</h3>
        <span class="heart">♡</span>
      </div>
      <p class="code">{{ cat.code }}</p>

      <div class="meta">
        <span>{{ cat.coatColor }}</span>
        <span>{{ cat.ageStage }}</span>
        <span>{{ cat.gender }}</span>
      </div>

      <div class="tags">
        <el-tag v-for="tag in cat.personalityTags" :key="tag" size="small" effect="plain">
          {{ tag }}
        </el-tag>
      </div>

      <div class="footer">
        <span class="health">{{ cat.healthStatus }}</span>
        <span>{{ cat.lastSeenLocation }}</span>
      </div>
    </div>
  </RouterLink>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { Cat } from '@/types/cat';

const props = defineProps<{
  cat: Cat;
}>();

const statusType = computed(() => {
  if (props.cat.adoptionStatus === '已领养') {
    return 'success';
  }

  if (props.cat.adoptionStatus === '暂不开放') {
    return 'warning';
  }

  return 'danger';
});
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;
@use '@/assets/styles/mixins' as *;

.cat-card {
  @include card-shell(20px);
  @include hover-lift;
  display: block;
  overflow: hidden;
  color: inherit;
}

.cover {
  position: relative;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: $color-primary-light;
}

.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.status {
  position: absolute;
  right: 12px;
  bottom: 12px;
}

.body {
  padding: 16px;
}

.title-row,
.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

h3 {
  margin: 0;
  color: $color-text;
  font-size: 19px;
}

.heart {
  color: #f97316;
  font-size: 22px;
}

.code,
.footer {
  color: $color-text-secondary;
  font-size: 12px;
}

.code {
  margin: 6px 0 12px;
}

.meta,
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.meta span {
  padding: 5px 9px;
  border-radius: 999px;
  background: #fff7ed;
  color: $color-text-secondary;
  font-size: 12px;
}

.tags {
  margin: 12px 0 14px;
}

.health {
  color: #15803d;
  font-weight: 700;
}
</style>
