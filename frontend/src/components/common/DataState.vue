<template>
  <div class="data-state" :class="type">
    <el-skeleton v-if="type === 'loading'" :rows="rows" animated />
    <template v-else>
      <div class="icon">{{ icon }}</div>
      <h3>{{ title }}</h3>
      <p>{{ description }}</p>
      <el-button v-if="actionText" round @click="$emit('retry')">{{ actionText }}</el-button>
    </template>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    type: 'loading' | 'error';
    title?: string;
    description?: string;
    actionText?: string;
    rows?: number;
  }>(),
  {
    title: '加载失败',
    description: '数据暂时无法获取，请稍后再试。',
    actionText: '',
    rows: 5,
  },
);

defineEmits<{
  retry: [];
}>();

const icon = '!';
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;
@use '@/assets/styles/mixins' as *;

.data-state {
  @include card-shell(20px);
  padding: 24px;
}

.error {
  display: grid;
  min-height: 220px;
  place-items: center;
  align-content: center;
  text-align: center;
}

.icon {
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  border-radius: 50%;
  background: rgba(248, 113, 113, 0.14);
  color: #dc2626;
  font-size: 24px;
  font-weight: 900;
}

h3 {
  margin: 12px 0 6px;
  color: $color-text;
}

p {
  margin: 0 0 16px;
  color: $color-text-secondary;
}
</style>
