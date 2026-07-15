import { defineStore } from 'pinia';
import { login, logout, register } from '@/api/auth';
import type { LoginPayload, RegisterPayload, UserProfile } from '@/types/user';
import { getStorage, setStorage } from '@/utils/storage';

interface UserState {
  profile: UserProfile | null;
  token: string;
}

const AUTH_TOKEN_KEY = 'cattrace_token';
const AUTH_PROFILE_KEY = 'cattrace_profile';

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    profile: getStorage<UserProfile | null>(AUTH_PROFILE_KEY, null),
    token: getStorage<string>(AUTH_TOKEN_KEY, ''),
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token && state.profile),
    isAdmin: (state) => state.profile?.role === 'admin',
    isUser: (state) => state.profile?.role === 'user',
    displayName: (state) => state.profile?.nickname || '访客',
  },
  actions: {
    persistAuth(result: { token: string; profile: UserProfile }) {
      this.token = result.token;
      this.profile = result.profile;
      setStorage(AUTH_TOKEN_KEY, result.token);
      setStorage(AUTH_PROFILE_KEY, result.profile);
    },
    async login(payload: LoginPayload) {
      const result = await login(payload);
      this.persistAuth(result);
      return result.profile;
    },
    async register(payload: RegisterPayload) {
      const result = await register(payload);
      this.persistAuth(result);
      return result.profile;
    },
    async logout() {
      await logout();
      this.token = '';
      this.profile = null;
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem(AUTH_PROFILE_KEY);
    },
  },
});
