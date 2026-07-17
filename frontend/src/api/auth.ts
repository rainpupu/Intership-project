import request from '@/api/request';
import type {
  AuthResult,
  CreateAdminPayload,
  LoginPayload,
  RegisterPayload,
  UpdateProfilePayload,
  UpdateUserRolePayload,
  UserListQuery,
  UserProfile,
} from '@/types/user';

interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

interface BackendUserProfile {
  id: number | string;
  username: string;
  nickname?: string | null;
  avatar?: string | null;
  role: UserProfile['role'];
  email: string;
  phone?: string | null;
  campusRole?: string | null;
  bio?: string | null;
}

interface BackendAuthResult {
  token: string;
  profile: BackendUserProfile;
}

function normalizeProfile(profile: BackendUserProfile): UserProfile {
  const pendingEmail = profile.email.endsWith('@pending.cattrace.local');

  return {
    id: String(profile.id),
    username: profile.username,
    nickname: profile.nickname || '',
    avatar: profile.avatar || 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?auto=format&fit=crop&w=200&q=80',
    role: profile.role,
    email: pendingEmail ? '' : profile.email,
    phone: profile.phone || '',
    campusRole: profile.campusRole || '',
    bio: profile.bio || '',
  };
}

function normalizeAuthResult(result: BackendAuthResult): AuthResult {
  return {
    token: result.token,
    profile: normalizeProfile(result.profile),
  };
}

export async function login(payload: LoginPayload): Promise<AuthResult> {
  const response = await request.post<ApiResponse<BackendAuthResult>, ApiResponse<BackendAuthResult>>('/auth/login', payload);
  return normalizeAuthResult(response.data);
}

export async function register(payload: RegisterPayload): Promise<AuthResult> {
  const response = await request.post<ApiResponse<BackendAuthResult>, ApiResponse<BackendAuthResult>>('/auth/register', payload);
  return normalizeAuthResult(response.data);
}

export async function getCurrentUser(_token: string): Promise<UserProfile | undefined> {
  const response = await request.get<ApiResponse<BackendUserProfile>, ApiResponse<BackendUserProfile>>('/auth/me');
  return normalizeProfile(response.data);
}

export async function logout(): Promise<{ success: boolean }> {
  await request.post('/auth/logout');
  return { success: true };
}

export async function updateUserProfile(_profile: UserProfile, payload: UpdateProfilePayload): Promise<UserProfile> {
  const response = await request.put<ApiResponse<BackendUserProfile>, ApiResponse<BackendUserProfile>>('/auth/profile', payload);
  return normalizeProfile(response.data);
}

export async function getUserList(query: UserListQuery = { role: 'all' }): Promise<UserProfile[]> {
  const response = await request.get<ApiResponse<BackendUserProfile[]>, ApiResponse<BackendUserProfile[]>>('/auth/users', {
    params: query,
  });
  return response.data.map(normalizeProfile);
}

export async function getAdminList(): Promise<UserProfile[]> {
  const response = await request.get<ApiResponse<BackendUserProfile[]>, ApiResponse<BackendUserProfile[]>>('/auth/admins');
  return response.data.map(normalizeProfile);
}

export async function createAdmin(payload: CreateAdminPayload): Promise<UserProfile> {
  const response = await request.post<ApiResponse<BackendUserProfile>, ApiResponse<BackendUserProfile>>('/auth/admins', payload);
  return normalizeProfile(response.data);
}

export async function updateUserRole(payload: UpdateUserRolePayload): Promise<UserProfile | undefined> {
  const response = await request.put<ApiResponse<BackendUserProfile>, ApiResponse<BackendUserProfile>>(
    `/auth/users/${payload.userId}/role`,
    payload,
  );
  return normalizeProfile(response.data);
}
