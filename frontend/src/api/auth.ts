import { mockResolve } from '@/api/request';
import type {
  AuthResult,
  CreateAdminPayload,
  LoginPayload,
  RegisterPayload,
  UpdateProfilePayload,
  UpdateUserRolePayload,
  UserRole,
  UserListQuery,
  UserProfile,
} from '@/types/user';

const avatarMap = {
  user: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=200&q=80',
  admin: 'https://images.unsplash.com/photo-1560250097-0b93528c311a?auto=format&fit=crop&w=200&q=80',
  superAdmin: 'https://images.unsplash.com/photo-1547425260-76bcadfb4f2c?auto=format&fit=crop&w=200&q=80',
};

function buildProfile(username: string, nickname?: string, fixedRole?: Exclude<UserRole, 'visitor'>): UserProfile {
  const normalizedUsername = username.toLowerCase();
  const role = fixedRole || (normalizedUsername.includes('super') ? 'super_admin' : normalizedUsername.includes('admin') ? 'admin' : 'user');
  const isSuperAdmin = role === 'super_admin';
  const isAdmin = role === 'admin' || isSuperAdmin;

  return {
    id: isSuperAdmin ? 'super-admin-001' : isAdmin ? `admin-${username || 'mock'}` : `user-${username || 'mock'}`,
    username: username || (isSuperAdmin ? 'superadmin' : isAdmin ? 'admin' : 'user'),
    nickname: nickname || (isSuperAdmin ? '总管理员' : isAdmin ? '平台管理员' : '校园守护者'),
    avatar: isSuperAdmin ? avatarMap.superAdmin : isAdmin ? avatarMap.admin : avatarMap.user,
    role: isSuperAdmin ? 'super_admin' : isAdmin ? 'admin' : 'user',
    email: isSuperAdmin ? 'superadmin@cattrace.local' : isAdmin ? 'admin@cattrace.local' : 'volunteer@cattrace.local',
    phone: '',
    campusRole: isSuperAdmin ? '总管理员' : isAdmin ? '平台管理员' : '校园志愿者',
    bio: isSuperAdmin
      ? '负责全平台账号、管理员职责和数据范围管理。'
      : isAdmin
        ? '负责平台数据审核、识别任务和猫咪档案管理。'
        : '关注校园流浪猫，希望帮助它们建立稳定档案。',
  };
}

const mockUsers: UserProfile[] = [
  buildProfile('superadmin', undefined, 'super_admin'),
  buildProfile('admin', undefined, 'admin'),
  buildProfile('campus-admin', '东区管理员', 'admin'),
  buildProfile('user', '校园守护者', 'user'),
  buildProfile('volunteer-a', '西门志愿者', 'user'),
];

export function login(payload: LoginPayload): Promise<AuthResult> {
  return mockResolve({
    token: `mock-token-${payload.username}-${Date.now()}`,
    profile: buildProfile(payload.username),
  });
}

export function register(payload: RegisterPayload): Promise<AuthResult> {
  return mockResolve({
    token: `mock-token-${payload.username}-${Date.now()}`,
    profile: buildProfile(payload.username, payload.nickname, 'user'),
  });
}

export function getCurrentUser(token: string): Promise<UserProfile | undefined> {
  if (!token) {
    return mockResolve(undefined);
  }

  return mockResolve(buildProfile(token.includes('admin') ? 'admin' : 'user'));
}

export function logout(): Promise<{ success: boolean }> {
  return mockResolve({ success: true });
}

export function updateUserProfile(profile: UserProfile, payload: UpdateProfilePayload): Promise<UserProfile> {
  return mockResolve({
    ...profile,
    ...payload,
  });
}

export function getUserList(query: UserListQuery = { role: 'all' }): Promise<UserProfile[]> {
  const keyword = query.keyword?.trim().toLowerCase();
  const role = query.role || 'all';

  return mockResolve(
    mockUsers.filter((user) => {
      const matchRole = role === 'all' || user.role === role;
      const matchKeyword =
        !keyword ||
        user.username.toLowerCase().includes(keyword) ||
        user.nickname.toLowerCase().includes(keyword) ||
        user.email.toLowerCase().includes(keyword);

      return matchRole && matchKeyword;
    }),
  );
}

export function getAdminList(): Promise<UserProfile[]> {
  return getUserList({ role: 'admin' });
}

export function createAdmin(payload: CreateAdminPayload): Promise<UserProfile> {
  return mockResolve({
    id: `admin-${payload.username}`,
    username: payload.username,
    nickname: payload.nickname,
    avatar: avatarMap.admin,
    role: 'admin',
    email: payload.email,
    phone: payload.phone || '',
    campusRole: payload.campusRole,
    bio: '由总管理员创建的管理员账号。',
  });
}

export function updateUserRole(payload: UpdateUserRolePayload): Promise<UserProfile | undefined> {
  const target = mockUsers.find((user) => user.id === payload.userId);

  if (!target) {
    return mockResolve(undefined);
  }

  return mockResolve({
    ...target,
    role: payload.role,
    campusRole: payload.role === 'admin' ? '平台管理员' : '校园志愿者',
  });
}
