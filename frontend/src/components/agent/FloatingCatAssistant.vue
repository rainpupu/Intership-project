<template>
  <div class="floating-assistant" :class="{ open: isOpen }">
    <section v-if="isOpen" class="chat-window">
      <header class="chat-header">
        <div class="mini-pet" aria-hidden="true">
          <img :src="juziResting" alt="" />
        </div>
        <div>
          <strong>CatTrace AI</strong>
          <p>{{ currentBehavior.chatHint }}</p>
        </div>
        <button class="icon-button" type="button" aria-label="收起 AI 助手" @click="isOpen = false">×</button>
      </header>

      <div ref="messageListRef" class="message-list">
        <div v-for="message in messages" :key="message.id" class="message" :class="message.role">
          <span v-html="fmt(message.content)"></span>
        </div>
      </div>

      <div class="quick-questions">
        <button v-for="question in quickQuestions" :key="question" type="button" @click="sendPreset(question)">
          {{ question }}
        </button>
      </div>

      <div class="composer">
        <el-input v-model="draft" placeholder="问问小猫助手..." :disabled="sending" @keyup.enter="send" />
        <el-button type="primary" round :loading="sending" @click="send">发送</el-button>
      </div>
    </section>

    <button class="pet-launcher" type="button" :aria-label="isOpen ? '收起 AI 助手' : '打开 AI 助手'" @click="toggleOpen">
      <span v-if="!isOpen" class="status-bubble">
        <strong>{{ currentBehavior.label }}</strong>
        {{ currentBehavior.text }}
      </span>
      <span class="pet-stage" :class="currentBehavior.key" aria-hidden="true">
        <img class="pet-image" :src="currentBehavior.image" :alt="`桌宠橘子${currentBehavior.label}`" />
        <span class="pet-shadow"></span>
      </span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from 'vue';
import { sendAgentMessageStream, type AgentMessage } from '@/api/agent';
import juziGrooming from '@/assets/images/pet/juzi-grooming.webp';
import juziPlaying from '@/assets/images/pet/juzi-playing.webp';
import juziResting from '@/assets/images/pet/juzi-resting.webp';
import juziWalking from '@/assets/images/pet/juzi-walking.webp';

interface CatBehavior {
  key: 'walking' | 'playing' | 'resting' | 'grooming';
  label: string;
  text: string;
  chatHint: string;
  image: string;
}

const behaviors: CatBehavior[] = [
  { key: 'walking', label: '巡逻中', text: '橘子正在页面边角散步', chatHint: '橘子巡逻回来，可以继续咨询', image: juziWalking },
  { key: 'playing', label: '玩耍中', text: '橘子正在追毛线球', chatHint: '橘子玩得正开心，也能帮你查猫咪', image: juziPlaying },
  { key: 'resting', label: '休息中', text: '橘子在打盹，轻点叫醒', chatHint: '橘子醒来啦，可以帮你整理建议', image: juziResting },
  { key: 'grooming', label: '舔毛中', text: '橘子正在认真整理毛毛', chatHint: '橘子整理好毛发，也整理好档案', image: juziGrooming },
];

const quickQuestions = ['推荐新手猫咪', '哪些需要关注', '领养注意事项'];
const behaviorIndex = ref(0);
const draft = ref('');
const isOpen = ref(false);
const sending = ref(false);
const messageListRef = ref<HTMLDivElement>();
const messages = ref<AgentMessage[]>([
  { id: 'float-welcome', role: 'assistant', content: '我是右下角的橘子助手，可以帮你快速查看猫咪状态、领养建议和重点关注名单。', createdAt: new Date().toISOString() },
]);

const currentBehavior = computed(() => behaviors[behaviorIndex.value]);

const behaviorTimer = window.setInterval(() => {
  if (!isOpen.value) { behaviorIndex.value = (behaviorIndex.value + 1) % behaviors.length; }
}, 6200);

function toggleOpen() {
  isOpen.value = !isOpen.value;
  if (isOpen.value) { scrollToBottom(); }
}

async function scrollToBottom() {
  await nextTick();
  if (messageListRef.value) { messageListRef.value.scrollTop = messageListRef.value.scrollHeight; }
}


function fmt(t) {
  if (!t) return '';
  let s = t;
  s = s.replace(/\t/g, '');
  s = s.replace(/\r/g, '');
  // Tables
  s = s.replace(/((?:\|.+\|\n)+)/g, function(m) {
    var lines = m.trim().split('\n');
    var h = '<table>';
    for (var i = 0; i < lines.length; i++) {
      if (lines[i].match(/^\|[-:\s|]+\|$/)) continue;
      var cells = lines[i].split('|').filter(function(c) { return c.trim(); });
      var tag = i === 0 ? 'th' : 'td';
      h += '<tr>' + cells.map(function(c) { return '<' + tag + '>' + c.trim() + '</' + tag + '>'; }).join('') + '</tr>';
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
    id: `float-user-${Date.now()}`,
    role: 'user',
    content,
    createdAt: new Date().toISOString(),
  });
  draft.value = '';
  sending.value = true;

  const id = `float-assistant-${Date.now()}`;
  const msg: AgentMessage = { id, role: 'assistant', content: '', createdAt: new Date().toISOString() };
  messages.value.push(msg);

  try {
    await sendAgentMessageStream(content, {
      onToken(token) {
        msg.content += token;
        messages.value = [...messages.value];
      },
      onDone() {
        sending.value = false;
        scrollToBottom();
      },
      onError(err) {
        msg.content = '出错了: ' + err;
        sending.value = false;
      },
    });
  } catch (e) {
    sending.value = false;
  }
}

onBeforeUnmount(() => { window.clearInterval(behaviorTimer); });
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;
@use '@/assets/styles/mixins' as *;

.floating-assistant {
  position: fixed;
  z-index: 50;
  right: 20px;
  bottom: 18px;
  display: grid;
  justify-items: end;
  gap: 12px;
  pointer-events: none;
}

.chat-window,
.pet-launcher {
  pointer-events: auto;
}

.chat-window {
  @include card-shell(24px);
  display: grid;
  width: min(380px, calc(100vw - 32px));
  grid-template-rows: auto minmax(220px, 320px) auto auto;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(18px);
}

.chat-header {
  display: grid;
  grid-template-columns: 48px 1fr 32px;
  gap: 10px;
  align-items: center;
}

.chat-header strong {
  color: $color-text;
}

.chat-header p {
  margin: 3px 0 0;
  color: $color-text-secondary;
  font-size: 12px;
}

.mini-pet {
  display: grid;
  width: 48px;
  height: 48px;
  place-items: center;
  overflow: hidden;
  border: 2px solid rgba(251, 146, 60, 0.2);
  border-radius: 18px;
  background: linear-gradient(145deg, #fff7ed, #ffffff);
  box-shadow: 0 10px 24px rgba(180, 104, 48, 0.14);
}

.mini-pet img {
  width: 76px;
  height: 56px;
  object-fit: contain;
  transform: translateY(2px);
}

.icon-button {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 50%;
  background: rgba(251, 146, 60, 0.12);
  color: $color-primary-dark;
  cursor: pointer;
  font-size: 22px;
  line-height: 1;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: auto;
  padding: 6px;
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

.message span {
  max-width: 82%;
  padding: 10px 12px;
  border-radius: 16px;
  font-size: 13px;
  line-height: 1.55;
}

.assistant span {
  border: 1px solid rgba(251, 146, 60, 0.16);
  background: #fff7ed;
  color: $color-text;
}

.assistant :deep(table) {
  width: 100%%;
  margin: 6px 0;
  border-collapse: collapse;
  font-size: 12px;
}

.assistant :deep(th) {
  padding: 6px 8px;
  border: 1px solid rgba(251, 146, 60, 0.2);
  background: rgba(251, 146, 60, 0.1);
  text-align: left;
  font-weight: 700;
  white-space: nowrap;
}

.assistant :deep(td) {
  padding: 5px 8px;
  border: 1px solid rgba(251, 146, 60, 0.12);
  vertical-align: top;
}

.user span {
  background: $color-primary;
  color: #fff;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-questions button {
  padding: 7px 10px;
  border: 1px solid rgba(251, 146, 60, 0.22);
  border-radius: 999px;
  background: rgba(255, 247, 237, 0.82);
  color: $color-text-secondary;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
}

.composer {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
}

.pet-launcher {
  position: relative;
  width: 224px;
  height: 172px;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.status-bubble {
  position: absolute;
  right: 150px;
  bottom: 108px;
  z-index: 2;
  display: grid;
  width: max-content;
  max-width: 210px;
  gap: 2px;
  padding: 9px 12px;
  border: 1px solid rgba(251, 146, 60, 0.18);
  border-radius: 16px 16px 4px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: $shadow-soft;
  color: $color-text;
  font-size: 12px;
  line-height: 1.35;
  text-align: left;
  white-space: nowrap;
}

.status-bubble strong {
  color: $color-primary-dark;
  font-size: 11px;
}

.pet-stage {
  position: absolute;
  right: 0;
  bottom: 0;
  display: grid;
  width: 210px;
  height: 160px;
  place-items: end center;
  transform-origin: center bottom;
}

.pet-image {
  position: relative;
  z-index: 1;
  width: 210px;
  height: 160px;
  object-fit: contain;
  object-position: center bottom;
  filter: drop-shadow(0 18px 18px rgba(120, 53, 15, 0.16));
  transform-origin: center bottom;
}

.pet-shadow {
  position: absolute;
  right: 30px;
  bottom: 2px;
  left: 34px;
  height: 16px;
  border-radius: 50%;
  background: rgba(180, 104, 48, 0.2);
  filter: blur(5px);
}

.walking {
  animation: pet-walk 3.2s ease-in-out infinite;
}

.walking .pet-image {
  animation: pet-step 0.72s ease-in-out infinite;
}

.playing .pet-image {
  animation: pet-play 1.45s ease-in-out infinite;
}

.playing .pet-shadow {
  animation: pet-shadow-pulse 1.45s ease-in-out infinite;
}

.resting .pet-image {
  animation: pet-breathe 3.2s ease-in-out infinite;
}

.grooming .pet-image {
  animation: pet-groom 1.45s ease-in-out infinite;
}

.open .pet-stage {
  transform: scale(0.9);
}

@keyframes pet-walk {
  0%,
  100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(-16px);
  }
}

@keyframes pet-step {
  0%,
  100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-4px) rotate(-1deg);
  }
}

@keyframes pet-play {
  0%,
  100% {
    transform: translateY(0) rotate(0deg) scale(1);
  }
  45% {
    transform: translateY(-6px) rotate(-2deg) scale(1.03);
  }
  70% {
    transform: translateY(1px) rotate(1deg) scale(0.99);
  }
}

@keyframes pet-breathe {
  0%,
  100% {
    transform: scaleY(1);
  }
  50% {
    transform: scaleY(0.975) translateY(2px);
  }
}

@keyframes pet-groom {
  0%,
  100% {
    transform: rotate(0deg);
  }
  45% {
    transform: rotate(-2deg) translateY(2px);
  }
  70% {
    transform: rotate(1deg);
  }
}

@keyframes pet-shadow-pulse {
  0%,
  100% {
    transform: scaleX(1);
    opacity: 1;
  }
  50% {
    transform: scaleX(0.88);
    opacity: 0.7;
  }
}

@media (max-width: 620px) {
  .floating-assistant {
    right: 8px;
    bottom: 8px;
  }

  .chat-window {
    width: calc(100vw - 16px);
    grid-template-rows: auto minmax(180px, 280px) auto auto;
  }

  .pet-launcher {
    width: 168px;
    height: 130px;
  }

  .pet-stage,
  .pet-image {
    width: 160px;
    height: 122px;
  }

  .status-bubble {
    display: none;
  }

  .composer {
    grid-template-columns: 1fr;
  }
}
</style>
