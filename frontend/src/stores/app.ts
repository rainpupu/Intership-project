import { defineStore } from 'pinia';

export const useAppStore = defineStore('app', {
  state: () => ({
    brandName: 'CatTrace Agent',
    sidebarCollapsed: false,
  }),
  actions: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed;
    },
  },
});
