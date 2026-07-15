<template>
  <footer class="app-footer">
    <span>CatTrace Agent</span>
    <span>让科技不再冰冷，让爱有迹可循</span>
  </footer>
</template>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.app-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 28px 16px 36px;
  color: $color-text-secondary;
  font-size: 13px;
}

.app-footer span:first-child {
  color: $color-text;
  font-weight: 800;
}
</style>
