<template>
  <main class="impersonation-entry">
    <el-result
      :icon="statusIcon"
      :title="statusTitle"
      :sub-title="statusMessage"
    >
      <template #extra>
        <el-button v-if="failed" type="primary" round @click="router.replace('/login')">返回登录页</el-button>
      </template>
    </el-result>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/user';
import type { AuthResult } from '@/types/user';

const router = useRouter();
const userStore = useUserStore();
const failed = ref(false);
const statusMessage = ref('正在进入用户端视图...');

const statusIcon = computed(() => (failed.value ? 'error' : 'info'));
const statusTitle = computed(() => (failed.value ? '进入用户端失败' : '正在进入用户端'));

function parseImpersonationPayload(): AuthResult | null {
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ''));
  const token = params.get('token');
  const rawProfile = params.get('profile');
  if (!token || !rawProfile) return null;

  try {
    return {
      token,
      profile: JSON.parse(rawProfile),
    };
  } catch {
    return null;
  }
}

onMounted(async () => {
  const payload = parseImpersonationPayload();
  if (!payload || payload.profile.role !== 'user') {
    failed.value = true;
    statusMessage.value = '访问参数无效，请从管理端重新打开。';
    return;
  }

  userStore.persistImpersonation(payload);
  window.history.replaceState(null, '', '/');
  await router.replace('/');
});
</script>

<style scoped lang="scss">
.impersonation-entry {
  display: grid;
  min-height: 100vh;
  place-items: center;
  background: #fff7ed;
}
</style>
