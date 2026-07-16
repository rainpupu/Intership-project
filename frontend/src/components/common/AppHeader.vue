<template>
  <header class="app-header">
    <RouterLink class="brand" to="/">
      <span class="brand-icon">🐱</span>
      <span>CatTrace Agent</span>
    </RouterLink>

    <nav class="nav">
      <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-link">
        {{ item.label }}
      </RouterLink>
    </nav>

    <div class="header-actions">
      <el-input class="search" placeholder="搜索猫咪、地点、线索..." clearable />
      <RouterLink v-if="userStore.isAdmin" to="/admin/dashboard">
        <el-button round>管理端</el-button>
      </RouterLink>
      <RouterLink v-if="userStore.isLoggedIn" to="/recognition">
        <el-button round>我的识别</el-button>
      </RouterLink>
      <RouterLink v-if="!userStore.isLoggedIn" to="/login">
        <el-button round>登录</el-button>
      </RouterLink>
      <RouterLink v-if="!userStore.isLoggedIn" to="/register">
        <el-button type="primary" round>注册</el-button>
      </RouterLink>
      <el-dropdown v-else trigger="click" @command="handleCommand">
        <button class="user-entry" type="button">
          <img :src="userStore.profile?.avatar" :alt="userStore.displayName" />
          <span>{{ userStore.displayName }}</span>
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人信息</el-dropdown-item>
            <el-dropdown-item command="recognition">我的识别</el-dropdown-item>
            <el-dropdown-item v-if="userStore.isAdmin" command="admin">管理端</el-dropdown-item>
            <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useUserStore } from '@/stores/user';

const router = useRouter();
const userStore = useUserStore();

const navItems = computed(() => [
  { label: '首页', path: '/' },
  { label: '猫咪图鉴', path: '/cats' },
  { label: 'AI 助手', path: '/chat' },
  { label: '我的识别', path: '/recognition' },
]);

async function handleCommand(command: string) {
  if (command === 'logout') {
    await userStore.logout();
    await router.push('/');
    return;
  }

  if (command === 'admin') {
    await router.push('/admin/dashboard');
    return;
  }

  if (command === 'profile') {
    await router.push('/profile');
    return;
  }

  await router.push('/recognition');
}
</script>

<style scoped lang="scss">
@use '@/assets/styles/variables' as *;

.app-header {
  position: sticky;
  z-index: 20;
  top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 22px;
  min-height: 72px;
  padding: 0 32px;
  border-bottom: 1px solid rgba(251, 146, 60, 0.16);
  background: rgba(255, 250, 243, 0.82);
  backdrop-filter: blur(18px);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: $color-text;
  font-size: 18px;
  font-weight: 800;
  white-space: nowrap;
}

.brand-icon {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 10px 24px rgba(251, 146, 60, 0.15);
}

.nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 26px;
  flex: 1;
}

.nav-link {
  position: relative;
  color: $color-text-secondary;
  font-size: 14px;
  font-weight: 700;

  &.router-link-active {
    color: $color-primary-dark;
  }

  &.router-link-active::after {
    position: absolute;
    right: 0;
    bottom: -12px;
    left: 0;
    height: 3px;
    border-radius: 999px;
    background: $color-primary;
    content: '';
  }
}

.header-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-width: 0;
  gap: 10px;
}

.search {
  width: 220px;
}

.user-entry {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px 6px 6px;
  border: 1px solid rgba(251, 146, 60, 0.16);
  border-radius: 999px;
  background: #fff;
  color: $color-text;
  cursor: pointer;
  font-weight: 700;
}

.user-entry img {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  object-fit: cover;
}

@media (max-width: 1080px) {
  .search {
    display: none;
  }
}

@media (max-width: 900px) {
  .nav {
    display: none;
  }

  .app-header {
    align-items: flex-start;
    flex-direction: column;
    padding: 0 18px;
    padding-block: 14px;
  }

  .header-actions {
    width: 100%;
    flex-wrap: wrap;
    justify-content: flex-start;
  }
}
</style>
