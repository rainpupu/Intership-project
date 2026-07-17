<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <RouterLink class="brand" to="/">
        <span>🐱</span>
        <strong>CatTrace Agent</strong>
      </RouterLink>

      <nav>
        <RouterLink v-for="item in menuItems" :key="item.path" :to="item.path" class="menu-link">
          <span>{{ item.icon }}</span>
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>

    <section class="admin-main">
      <header class="admin-topbar">
        <div>
          <strong>管理端</strong>
          <span>管理员可查看全平台识别记录、猫咪档案和运营数据</span>
        </div>
        <div class="topbar-actions">
          <span class="role-badge">管理员：{{ userStore.displayName }}</span>
          <RouterLink to="/">
            <el-button round>返回用户端</el-button>
          </RouterLink>
          <el-button round @click="handleLogout">退出</el-button>
        </div>
      </header>

      <RouterView />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/user';

const router = useRouter();
const userStore = useUserStore();

const menuItems = computed(() => {
  const items = [
    { label: '数据概览', path: '/admin/dashboard', icon: '📊' },
    { label: '识别任务', path: '/admin/recognition', icon: '🧠' },
    { label: '猫咪管理', path: '/admin/cats', icon: '🐾' },
  ];

  if (userStore.isSuperAdmin) {
    items.push({ label: '账号管理', path: '/admin/users', icon: '👤' });
  }

  return items;
});

async function handleLogout() {
  await userStore.logout();
  await router.push('/login');
}
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
