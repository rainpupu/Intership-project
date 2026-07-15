import type { RouteRecordRaw } from 'vue-router';

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/layouts/UserLayout.vue'),
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/user/Home.vue'),
      },
      {
        path: 'cats',
        name: 'CatGallery',
        component: () => import('@/views/user/CatGallery.vue'),
      },
      {
        path: 'cats/:id',
        name: 'CatDetail',
        component: () => import('@/views/user/CatDetail.vue'),
      },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/user/Chat.vue'),
      },
      {
        path: 'recognition',
        name: 'UserRecognition',
        component: () => import('@/views/user/UserRecognition.vue'),
        meta: {
          requiresAuth: true,
          roles: ['user', 'admin'],
        },
      },
      {
        path: 'login',
        name: 'Login',
        component: () => import('@/views/auth/Login.vue'),
      },
      {
        path: 'register',
        name: 'Register',
        component: () => import('@/views/auth/Register.vue'),
      },
    ],
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    redirect: '/admin/dashboard',
    meta: {
      requiresAuth: true,
      roles: ['admin'],
    },
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: {
          requiresAuth: true,
          roles: ['admin'],
        },
      },
      {
        path: 'recognition',
        name: 'AdminRecognition',
        component: () => import('@/views/admin/Recognition.vue'),
        meta: {
          requiresAuth: true,
          roles: ['admin'],
        },
      },
      {
        path: 'cats',
        name: 'AdminCatManage',
        component: () => import('@/views/admin/CatManage.vue'),
        meta: {
          requiresAuth: true,
          roles: ['admin'],
        },
      },
    ],
  },
];
