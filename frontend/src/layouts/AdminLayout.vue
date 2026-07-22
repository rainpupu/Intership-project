<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <RouterLink class="brand" to="/admin/dashboard">
        <span>🐱</span>
        <strong>CatTrace Agent</strong>
      </RouterLink>

      <nav>
        <RouterLink v-for="item in menuItems" :key="item.path" :to="item.path" class="menu-link">
          <span>{{ item.icon }}</span>
          {{ item.label }}
          <el-badge
            v-if="item.path === '/admin/clues'"
            :value="pendingClueCount"
            :hidden="pendingClueCount === 0"
            class="menu-badge"
          >
            <span class="badge-anchor"></span>
          </el-badge>
        </RouterLink>
      </nav>
    </aside>

    <section class="admin-main">
      <header class="admin-topbar">
        <div>
          <strong>管理端</strong>
          <span>集中查看识别记录、猫咪档案、云领养订单和运营数据</span>
        </div>
        <div class="topbar-actions">
          <RouterLink class="admin-avatar-link" to="/admin/clues" title="待审核线索">
            <el-badge :value="pendingClueCount" :hidden="pendingClueCount === 0">
              <img class="admin-avatar" :src="userStore.profile?.avatar" :alt="userStore.displayName" />
            </el-badge>
          </RouterLink>
          <span class="role-badge">管理员：{{ userStore.displayName }}</span>
          <el-button type="primary" round :loading="impersonating" @click="handleImpersonation">
            模拟用户
          </el-button>
          <el-button round @click="handleLogout">退出</el-button>
        </div>
      </header>

      <RouterView />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { createSelfImpersonation } from '@/api/auth';
import { getRequestErrorMessage } from '@/api/request';
import { getPendingClueCount } from '@/api/recognition';
import { useUserStore } from '@/stores/user';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const pendingClueCount = ref(0);
const impersonating = ref(false);

const menuItems = computed(() => {
  const items = [
    { label: '数据概览', path: '/admin/dashboard', icon: '📊' },
    { label: '识别任务', path: '/admin/recognition', icon: '🧠' },
    { label: '线索审核', path: '/admin/clues', icon: '🔔' },
    { label: '猫咪档案', path: '/admin/cats', icon: '🐾' },
    { label: '云领养订单', path: '/admin/cloud-adoptions', icon: '🎁' },
  ];

  if (userStore.isSuperAdmin) {
    items.push({ label: '账号管理', path: '/admin/users', icon: '👥' });
  }

  return items;
});

async function handleLogout() {
  await userStore.logout();
  await router.push('/login');
}

async function handleImpersonation() {
  const popup = window.open('', '_blank');
  if (!popup) {
    ElMessage.warning('浏览器阻止了新窗口，请允许弹出窗口后重试');
    return;
  }

  popup.document.write('<p style="font-family: sans-serif; padding: 24px;">正在打开模拟用户视图...</p>');
  impersonating.value = true;
  try {
    const result = await createSelfImpersonation();
    const params = new URLSearchParams({
      token: result.token,
      profile: JSON.stringify(result.profile),
    });
    popup.location.href = `${window.location.origin}/impersonate#${params.toString()}`;
    ElMessage.success('已打开当前管理员的专属模拟用户窗口');
  } catch (error) {
    popup.close();
    ElMessage.error(getRequestErrorMessage(error, '模拟用户窗口创建失败'));
  } finally {
    impersonating.value = false;
  }
}

async function refreshPendingClueCount() {
  if (!userStore.isAdmin) {
    pendingClueCount.value = 0;
    return;
  }

  try {
    pendingClueCount.value = await getPendingClueCount();
  } catch {
    pendingClueCount.value = 0;
  }
}

onMounted(() => {
  refreshPendingClueCount();
  window.addEventListener('cattrace:pending-clues-updated', refreshPendingClueCount);
});

watch(
  () => route.fullPath,
  () => refreshPendingClueCount(),
);

onBeforeUnmount(() => {
  window.removeEventListener('cattrace:pending-clues-updated', refreshPendingClueCount);
});
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;
@use '@/assets/styles/mixins' as *;

.admin-layout {
  display: grid;
  grid-template-columns: 236px 1fr;
  min-height: 100vh;
  @include page-bg;
}

.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  padding: 24px 18px;
  border-right: 1px solid rgba(251, 146, 60, 0.16);
  background: rgba(255, 255, 255, 0.74);
  backdrop-filter: blur(18px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 34px;
  color: $color-text;
}

.brand span {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  border-radius: 14px;
  background: #fff7ed;
}

nav {
  display: grid;
  gap: 10px;
}

.menu-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 13px 14px;
  border-radius: 16px;
  color: $color-text-secondary;
  font-weight: 700;

  &.router-link-active {
    background: rgba(251, 146, 60, 0.14);
    color: $color-primary-dark;
  }
}

.menu-badge {
  margin-left: auto;
}

.badge-anchor {
  display: block;
  width: 1px;
  height: 1px;
}

.admin-main {
  min-width: 0;
}

.admin-topbar {
  position: sticky;
  z-index: 10;
  top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  min-height: 72px;
  padding: 0 28px;
  border-bottom: 1px solid rgba(251, 146, 60, 0.14);
  background: rgba(255, 250, 243, 0.78);
  backdrop-filter: blur(16px);
}

.admin-topbar div:first-child {
  display: grid;
  gap: 4px;
}

.admin-topbar strong {
  color: $color-text;
}

.admin-topbar span {
  color: $color-text-secondary;
  font-size: 13px;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.admin-avatar-link {
  display: inline-flex;
  align-items: center;
}

.admin-avatar {
  width: 38px;
  height: 38px;
  border: 2px solid #fff;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 10px 20px rgba(251, 146, 60, 0.14);
}

.role-badge {
  padding: 9px 12px;
  border-radius: 999px;
  background: rgba(251, 146, 60, 0.12);
  color: $color-primary-dark !important;
  font-weight: 800;
}

@media (max-width: 900px) {
  .admin-layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: static;
    height: auto;
  }

  nav {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .admin-topbar,
  .topbar-actions {
    align-items: flex-start;
    flex-direction: column;
    padding: 18px;
  }
}
</style>
