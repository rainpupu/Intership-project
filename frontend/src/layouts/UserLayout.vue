<template>
  <div class="user-layout">
    <AppHeader v-if="!route.meta.hideHeader" />
    <RouterView />
    <AppFooter />
    <FloatingCatAssistant />
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';
import AppFooter from '@/components/common/AppFooter.vue';
import AppHeader from '@/components/common/AppHeader.vue';
import FloatingCatAssistant from '@/components/agent/FloatingCatAssistant.vue';

const route = useRoute();
</script>

<style scoped lang="scss">
@use '@/assets/styles/mixins' as *;

.user-layout {
  min-height: 100vh;
  @include page-bg;
}
</style>
