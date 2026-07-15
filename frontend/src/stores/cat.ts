import { defineStore } from 'pinia';
import { getCatList } from '@/api/cat';
import type { Cat } from '@/types/cat';

export const useCatStore = defineStore('cat', {
  state: () => ({
    cats: [] as Cat[],
    loading: false,
  }),
  getters: {
    focusCats: (state) => state.cats.filter((cat) => cat.isFocus),
    adoptionOpenCats: (state) => state.cats.filter((cat) => cat.adoptionStatus === '待领养'),
  },
  actions: {
    async fetchCats() {
      this.loading = true;
      try {
        this.cats = await getCatList();
      } finally {
        this.loading = false;
      }
    },
  },
});
