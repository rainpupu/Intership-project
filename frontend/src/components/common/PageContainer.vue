<template>
  <main class="page-container">
    <slot />
  </main>
</template>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.page-container {
  width: min(100% - 32px, $layout-width);
  margin: 0 auto;
  padding: 34px 0 54px;
}
</style>
