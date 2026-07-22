import type { RouteRecordRaw } from 'vue-router';

export const routes: RouteRecordRaw[] = [
  {
    path: '/impersonate',
    name: 'ImpersonationEntry',
    component: () => import('@/views/auth/ImpersonationEntry.vue'),
  },
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
          roles: ['user'],
        },
      },
      {
        path: 'profile',
        name: 'UserProfile',
        component: () => import('@/views/user/Profile.vue'),
        meta: {
          requiresAuth: true,
          roles: ['user'],
          hideHeader: true,
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
      roles: ['admin', 'super_admin'],
    },
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/Dashboard.vue'),
        meta: {
          requiresAuth: true,
          roles: ['admin', 'super_admin'],
        },
      },
      {
        path: 'recognition',
        name: 'AdminRecognition',
        component: () => import('@/views/admin/Recognition.vue'),
        meta: {
          requiresAuth: true,
          roles: ['admin', 'super_admin'],
        },
      },
      {
        path: 'clues',
        name: 'AdminClueReview',
        component: () => import('@/views/admin/ClueReview.vue'),
        meta: {
          requiresAuth: true,
          roles: ['admin', 'super_admin'],
        },
      },
      {
        path: 'cats',
        name: 'AdminCatManage',
        component: () => import('@/views/admin/CatManage.vue'),
        meta: {
          requiresAuth: true,
          roles: ['admin', 'super_admin'],
        },
      },
      {
        path: 'cloud-adoptions',
        name: 'AdminCloudAdoptions',
        component: () => import('@/views/admin/CloudAdoptionOrders.vue'),
        meta: {
          requiresAuth: true,
          roles: ['admin', 'super_admin'],
        },
      },
      {
        path: 'users',
        name: 'AdminUserManage',
        component: () => import('@/views/admin/UserManage.vue'),
        meta: {
          requiresAuth: true,
          roles: ['super_admin'],
        },
      },
    ],
  },
];
