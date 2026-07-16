import { defineStore } from 'pinia';

export const useAppStore = defineStore('app', {
  state: () => ({
    brandName: 'CatTrace Agent',
    sidebarCollapsed: false,
    profileReturnPath: '/',
  }),
  actions: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed;
    },
    setProfileReturnPath(path: string) {
      this.profileReturnPath = path || '/';
    },
  },
});
