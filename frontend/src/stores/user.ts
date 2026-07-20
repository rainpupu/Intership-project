import { defineStore } from 'pinia';
import { login, logout, register, updateUserProfile } from '@/api/auth';
import type { LoginPayload, RegisterPayload, UpdateProfilePayload, UserProfile } from '@/types/user';
import { getSessionStorage, getStorage, setSessionStorage, setStorage } from '@/utils/storage';

interface UserState {
  profile: UserProfile | null;
  token: string;
}

const AUTH_TOKEN_KEY = 'cattrace_token';
const AUTH_PROFILE_KEY = 'cattrace_profile';
const IMPERSONATION_FLAG_KEY = 'cattrace_impersonating';

function getInitialToken() {
  return getSessionStorage<string>(AUTH_TOKEN_KEY, '') || getStorage<string>(AUTH_TOKEN_KEY, '');
}

function getInitialProfile() {
  return getSessionStorage<UserProfile | null>(AUTH_PROFILE_KEY, null) || getStorage<UserProfile | null>(AUTH_PROFILE_KEY, null);
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    profile: getInitialProfile(),
    token: getInitialToken(),
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token && state.profile),
    isAdmin: (state) => state.profile?.role === 'admin' || state.profile?.role === 'super_admin',
    isSuperAdmin: (state) => state.profile?.role === 'super_admin',
    isUser: (state) => state.profile?.role === 'user',
    isImpersonating: () => sessionStorage.getItem(IMPERSONATION_FLAG_KEY) === 'true',
    displayName: (state) => state.profile?.nickname || '访客',
  },
  actions: {
    persistAuth(result: { token: string; profile: UserProfile }) {
      this.token = result.token;
      this.profile = result.profile;
      sessionStorage.removeItem(AUTH_TOKEN_KEY);
      sessionStorage.removeItem(AUTH_PROFILE_KEY);
      sessionStorage.removeItem(IMPERSONATION_FLAG_KEY);
      setStorage(AUTH_TOKEN_KEY, result.token);
      setStorage(AUTH_PROFILE_KEY, result.profile);
    },
    persistImpersonation(result: { token: string; profile: UserProfile }) {
      this.token = result.token;
      this.profile = result.profile;
      setSessionStorage(AUTH_TOKEN_KEY, result.token);
      setSessionStorage(AUTH_PROFILE_KEY, result.profile);
      sessionStorage.setItem(IMPERSONATION_FLAG_KEY, 'true');
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
    async updateProfile(payload: UpdateProfilePayload) {
      if (!this.profile) {
        throw new Error('用户未登录');
      }

      const profile = await updateUserProfile(this.profile, payload);
      this.profile = profile;
      if (sessionStorage.getItem(IMPERSONATION_FLAG_KEY) === 'true') {
        setSessionStorage(AUTH_PROFILE_KEY, profile);
      } else {
        setStorage(AUTH_PROFILE_KEY, profile);
      }
      return profile;
    },
    async logout() {
      await logout();
      this.token = '';
      this.profile = null;
      if (sessionStorage.getItem(IMPERSONATION_FLAG_KEY) === 'true') {
        sessionStorage.removeItem(AUTH_TOKEN_KEY);
        sessionStorage.removeItem(AUTH_PROFILE_KEY);
        sessionStorage.removeItem(IMPERSONATION_FLAG_KEY);
        return;
      }

      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem(AUTH_PROFILE_KEY);
    },
  },
});
