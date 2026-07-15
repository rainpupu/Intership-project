<template>
  <article class="status-card">
    <span class="icon">{{ icon }}</span>
    <div>
      <p>{{ label }}</p>
      <strong>{{ value }}</strong>
      <small v-if="hint">{{ hint }}</small>
    </div>
  </article>
</template>

<script setup lang="ts">
defineProps<{
  icon: string;
  label: string;
  value: string;
  hint?: string;
}>();
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;
@use '@/assets/styles/mixins' as *;

.status-card {
  @include card-shell(18px);
  display: flex;
  gap: 14px;
  align-items: flex-start;
  padding: 18px;
}

.icon {
  display: grid;
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 16px;
  background: $color-yellow;
  font-size: 22px;
}

p {
  margin: 0 0 6px;
  color: $color-text-secondary;
  font-size: 13px;
}

strong {
  display: block;
  color: $color-text;
  font-size: 18px;
}

small {
  display: block;
  margin-top: 5px;
  color: $color-text-secondary;
}
</style>
