<template>
  <div class="empty-state">
    <div class="empty-icon">🐾</div>
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  description: string;
}>();
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.empty-state {
  display: grid;
  min-height: 260px;
  place-items: center;
  padding: 34px;
  color: $color-text-secondary;
  text-align: center;
}

.empty-icon {
  font-size: 42px;
}

h3 {
  margin: 10px 0 6px;
  color: $color-text;
}

p {
  margin: 0;
}
</style>
