import { createRouter, createWebHistory } from 'vue-router';
import { ElMessage } from 'element-plus';
import { routes } from '@/router/routes';
import { useAppStore } from '@/stores/app';
import { useUserStore } from '@/stores/user';
import type { UserRole } from '@/types/user';

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return {
      top: 0,
    };
  },
});

router.beforeEach((to, from) => {
  const appStore = useAppStore();
  const userStore = useUserStore();
  const requiresAuth = Boolean(to.matched.some((record) => record.meta.requiresAuth));
  const roleRules = to.matched.flatMap((record) => (record.meta.roles || []) as UserRole[]);

  if (to.name === 'UserProfile' && from.fullPath !== to.fullPath) {
    appStore.setProfileReturnPath(from.fullPath || '/');
  }

  if ((to.name === 'Login' || to.name === 'Register') && userStore.isLoggedIn) {
    return userStore.isAdmin ? '/admin/dashboard' : '/';
  }

  if (to.name === 'ImpersonationEntry') {
    return true;
  }

  if (userStore.isLoggedIn && userStore.isAdmin && !to.path.startsWith('/admin')) {
    if (to.fullPath !== '/') {
      ElMessage.warning('管理员账号只能进入管理端，请使用模拟用户功能查看用户端页面');
    }
    return '/admin/dashboard';
  }

  if (!requiresAuth) {
    return true;
  }

  if (!userStore.isLoggedIn) {
    return {
      path: '/login',
      query: {
        redirect: to.fullPath,
      },
    };
  }

  if (roleRules.length > 0 && userStore.profile && !roleRules.includes(userStore.profile.role)) {
    ElMessage.warning('当前账号无权访问该页面');
    return '/';
  }

  return true;
});

export default router;
