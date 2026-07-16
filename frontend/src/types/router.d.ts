import 'vue-router';
import type { UserRole } from '@/types/user';

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean;
    roles?: UserRole[];
    hideHeader?: boolean;
  }
}
