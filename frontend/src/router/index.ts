import { createRouter, createWebHistory } from 'vue-router';
import { routes } from '@/router/routes';
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

router.beforeEach((to) => {
  const userStore = useUserStore();
  const requiresAuth = Boolean(to.matched.some((record) => record.meta.requiresAuth));
  const roleRules = to.matched.flatMap((record) => (record.meta.roles || []) as UserRole[]);

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
    return userStore.isAdmin ? '/admin/dashboard' : '/recognition';
  }

  return true;
});

export default router;
