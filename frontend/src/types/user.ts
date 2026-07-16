export type UserRole = 'visitor' | 'user' | 'admin' | 'super_admin';

export interface UserProfile {
  id: string;
  username: string;
  nickname: string;
  avatar: string;
  role: UserRole;
  email: string;
  phone: string;
  campusRole: string;
  bio: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  password: string;
  nickname: string;
}

export interface CreateAdminPayload {
  username: string;
  password: string;
  nickname: string;
  email: string;
  phone?: string;
  campusRole: string;
}

export interface UpdateUserRolePayload {
  userId: string;
  role: Extract<UserRole, 'user' | 'admin'>;
}

export interface UserListQuery {
  role?: Exclude<UserRole, 'visitor'> | 'all';
  keyword?: string;
}

export interface AuthResult {
  token: string;
  profile: UserProfile;
}

export interface UpdateProfilePayload {
  nickname: string;
  avatar: string;
  email: string;
  phone: string;
  campusRole: string;
  bio: string;
}
