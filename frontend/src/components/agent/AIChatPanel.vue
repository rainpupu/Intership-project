<template>
  <section class="chat-panel">
    <div class="messages">
      <div v-for="message in messages" :key="message.id" class="message" :class="message.role">
        <div class="bubble" v-html="fmt(message.content)"></div>
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
import { sendAgentMessageStream, type AgentMessage } from '@/api/agent';

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
const sending = ref(false);


function fmt(t: string) {
  if (!t) return '';
  let s = t;
  s = s.replace(/\t/g, '');
  s = s.replace(/\r/g, '');
  // Tables
  s = s.replace(/((?:\|.+\|\n)+)/g, function(m: string) {
    var lines = m.trim().split('\n');
    var h = '<table>';
    for (var i = 0; i < lines.length; i++) {
      if (lines[i].match(/^\|[-:\s|]+\|$/)) continue;
      var cells = lines[i].split('|').filter(function(c: string) { return c.trim(); });
      var tag = i === 0 ? 'th' : 'td';
      h += '<tr>' + cells.map(function(c: string) { return '<' + tag + '>' + c.trim() + '</' + tag + '>'; }).join('') + '</tr>';
    }
    h += '</table>';
    return h;
  });
  s = s.replace(/\n{3,}/g, '\n\n');
  s = s.replace(/### (.+)/g, '<h4>$1</h4>');
  s = s.replace(/## (.+)/g, '<h3>$1</h3>');
  s = s.replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
  s = s.replace(/\n\n/g, '<br><br>');
  s = s.replace(/\n/g, '<br>');
  return s;
}

async function sendPreset(question: string) {
  draft.value = question;
  await send();
}

async function send() {
  const content = draft.value.trim();
  if (!content || sending.value) return;

  messages.value.push({
    id: `user-${Date.now()}`,
    role: 'user',
    content,
    createdAt: new Date().toISOString(),
  });
  draft.value = '';
  sending.value = true;

  const id = `assistant-${Date.now()}`;
  const thinkingText = '正在思考...';
  const msg: AgentMessage = { id, role: 'assistant', content: thinkingText, createdAt: new Date().toISOString() };
  messages.value.push(msg);

  await sendAgentMessageStream(content, {
    onToken(token: string) {
      msg.content = msg.content === thinkingText ? token : msg.content + token;
      messages.value = [...messages.value];
    },
    onDone() { sending.value = false; },
    onError(err: string) {
      msg.content = '出错了: ' + err;
      sending.value = false;
    },
  });
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

.assistant .bubble :deep(table) {
  width: 100%%;
  margin: 8px 0;
  border-collapse: collapse;
  font-size: 13px;
}

.assistant .bubble :deep(th) {
  padding: 8px 12px;
  border: 1px solid rgba(251, 146, 60, 0.2);
  background: rgba(251, 146, 60, 0.1);
  text-align: left;
  font-weight: 700;
  white-space: nowrap;
}

.assistant .bubble :deep(td) {
  padding: 7px 12px;
  border: 1px solid rgba(251, 146, 60, 0.12);
  vertical-align: top;
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
