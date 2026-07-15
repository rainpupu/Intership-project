export type UserRole = 'visitor' | 'user' | 'admin';

export interface UserProfile {
  id: string;
  nickname: string;
  avatar: string;
  role: UserRole;
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

export interface AuthResult {
  token: string;
  profile: UserProfile;
}
