import type { AuthResult, LoginPayload, RegisterPayload, UserProfile } from '@/types/user';

const avatarMap = {
  user: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=200&q=80',
  admin: 'https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=200&q=80',
};

function buildProfile(username: string, nickname?: string): UserProfile {
  const isAdmin = username.toLowerCase().includes('admin');

  return {
    id: isAdmin ? 'admin-001' : `user-${username || 'mock'}`,
    nickname: nickname || (isAdmin ? '平台管理员' : '校园守护者'),
    avatar: isAdmin ? avatarMap.admin : avatarMap.user,
    role: isAdmin ? 'admin' : 'user',
  };
}

export function login(payload: LoginPayload): Promise<AuthResult> {
  return Promise.resolve({
    token: `mock-token-${payload.username}-${Date.now()}`,
    profile: buildProfile(payload.username),
  });
}

export function register(payload: RegisterPayload): Promise<AuthResult> {
  return Promise.resolve({
    token: `mock-token-${payload.username}-${Date.now()}`,
    profile: buildProfile(payload.username, payload.nickname),
  });
}

export function getCurrentUser(token: string): Promise<UserProfile | undefined> {
  if (!token) {
    return Promise.resolve(undefined);
  }

  return Promise.resolve(buildProfile(token.includes('admin') ? 'admin' : 'user'));
}

export function logout(): Promise<{ success: boolean }> {
  return Promise.resolve({ success: true });
}
