<template>
  <PageContainer>
    <section class="chat-head">
      <div>
        <h1 class="page-title">AI 助手</h1>
        <p class="page-subtitle">围绕猫咪档案、重点关注状态和领养事项提供智能问答。</p>
      </div>
      <div class="assistant-badge">🤖 CatTrace Agent</div>
    </section>

    <AIChatPanel />
  </PageContainer>
</template>

<script setup lang="ts">
import AIChatPanel from '@/components/agent/AIChatPanel.vue';
import PageContainer from '@/components/common/PageContainer.vue';
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.chat-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 22px;
}

.assistant-badge {
  padding: 12px 16px;
  border: 1px solid rgba(96, 165, 250, 0.3);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.7);
  color: $color-text;
  font-weight: 800;
}

@media (max-width: 680px) {
  .chat-head {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
