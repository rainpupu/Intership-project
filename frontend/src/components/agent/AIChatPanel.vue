<template>
  <section class="chat-panel">
    <div class="messages">
      <div v-for="message in messages" :key="message.id" class="message" :class="message.role">
        <div class="bubble">{{ message.content }}</div>
      </div>
    </div>

    <div class="preset-list">
      <el-button v-for="question in presetQuestions" :key="question" round @click="sendPreset(question)">
        {{ question }}
      </el-button>
    </div>

    <div class="composer">
      <el-input
        v-model="draft"
        placeholder="问问 AI 助手，例如：哪些猫咪适合新手领养？"
        size="large"
        @keyup.enter="send"
      />
      <el-button type="primary" size="large" round @click="send">发送</el-button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { sendAgentMessage, type AgentMessage } from '@/api/agent';

const presetQuestions = [
  '推荐适合第一次养猫的猫咪',
  '小橘最近状态怎么样',
  '哪些猫咪需要重点关注',
  '领养猫咪需要注意什么',
];

const messages = ref<AgentMessage[]>([
  {
    id: 'welcome',
    role: 'assistant',
    content: '你好，我是 CatTrace AI 助手。可以帮你筛选适合领养的猫咪、查看重点关注状态，或解释领养注意事项。',
    createdAt: new Date().toISOString(),
  },
]);
const draft = ref('');

async function sendPreset(question: string) {
  draft.value = question;
  await send();
}

async function send() {
  const content = draft.value.trim();

  if (!content) {
    return;
  }

  messages.value.push({
    id: `user-${Date.now()}`,
    role: 'user',
    content,
    createdAt: new Date().toISOString(),
  });
  draft.value = '';
  messages.value.push(await sendAgentMessage(content));
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;
@use '@/assets/styles/mixins' as *;

.chat-panel {
  @include card-shell(26px);
  display: grid;
  grid-template-rows: minmax(360px, 1fr) auto auto;
  gap: 18px;
  min-height: 620px;
  padding: 22px;
}

.messages {
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: auto;
  padding: 10px;
}

.message {
  display: flex;

  &.user {
    justify-content: flex-end;
  }

  &.assistant {
    justify-content: flex-start;
  }
}

.bubble {
  max-width: min(680px, 82%);
  padding: 14px 16px;
  border-radius: 18px;
  color: $color-text;
  line-height: 1.65;
}

.assistant .bubble {
  border: 1px solid rgba(251, 146, 60, 0.18);
  background: rgba(255, 247, 237, 0.86);
}

.user .bubble {
  background: linear-gradient(135deg, #fb923c, #f97316);
  color: #fff;
}

.preset-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.composer {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
}

@media (max-width: 680px) {
  .composer {
    grid-template-columns: 1fr;
  }
}
</style>
