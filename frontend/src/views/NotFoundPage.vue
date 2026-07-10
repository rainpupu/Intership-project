<template>
  <div class="not-found-page">
    <div class="not-found-content">
      <h1 class="error-code">404</h1>
      <p class="error-message">页面未找到</p>
      <p class="error-hint">您访问的页面不存在或已被移除</p>
      <el-button type="primary" @click="goHome">
        返回首页
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
function goHome() {
  router.push('/')
}
</script>

<style lang="scss" scoped>
.not-found-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: $bg-color;
}

.not-found-content {
  text-align: center;

  .error-code {
    font-size: 120px;
    font-weight: 700;
    color: $primary-color;
    margin: 0;
    line-height: 1;
  }

  .error-message {
    font-size: 24px;
    color: $text-primary;
    margin: $spacing-lg 0 $spacing-sm;
  }

  .error-hint {
    font-size: 14px;
    color: $text-secondary;
    margin: 0 0 $spacing-xl;
  }
}
</style>
