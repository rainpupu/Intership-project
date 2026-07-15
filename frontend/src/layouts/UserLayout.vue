<template>
  <div class="user-layout">
    <AppHeader />
    <RouterView />
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import AppFooter from '@/components/common/AppFooter.vue';
import AppHeader from '@/components/common/AppHeader.vue';
</script>

<style scoped lang="scss">
@use '@/assets/styles/mixins' as *;

.user-layout {
  min-height: 100vh;
  @include page-bg;
}
</style>
