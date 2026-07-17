<template>
  <RouterLink v-if="to" :to="to" class="stat-card" custom v-slot="{ navigate }">
    <article class="stat-card" @click="navigate">
      <span class="icon">{{ icon }}</span>
      <div>
        <p>{{ label }}</p>
        <strong>{{ value }}</strong>
        <small>{{ hint }}</small>
      </div>
    </article>
  </RouterLink>
  <article v-else class="stat-card">
    <span class="icon">{{ icon }}</span>
    <div>
      <p>{{ label }}</p>
      <strong>{{ value }}</strong>
      <small>{{ hint }}</small>
    </div>
  </article>
</template>

<script setup lang="ts">
import type { RouteLocationRaw } from 'vue-router';

defineProps<{
  label: string;
  value: string | number;
  hint: string;
  icon: string;
  to?: RouteLocationRaw;
}>();
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;
@use '@/assets/styles/mixins' as *;

.stat-card {
  @include card-shell(20px);
  @include hover-lift;
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 20px;
}

.icon {
  display: grid;
  width: 48px;
  height: 48px;
  place-items: center;
  border-radius: 18px;
  background: linear-gradient(135deg, $color-primary-light, #fff);
  font-size: 24px;
}

p,
small {
  margin: 0;
  color: $color-text-secondary;
}

strong {
  display: block;
  margin: 4px 0;
  color: $color-text;
  font-size: 26px;
}
</style>
