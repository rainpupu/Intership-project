import axios from 'axios';

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  withCredentials: true,
});

request.interceptors.request.use((config) => {
  const rawToken = sessionStorage.getItem('cattrace_token') || localStorage.getItem('cattrace_token');
  let token = rawToken || '';

  if (rawToken) {
    try {
      token = JSON.parse(rawToken) as string;
    } catch {
      token = rawToken;
    }
  }

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

request.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(error),
);

export default request;

export function getRequestErrorMessage(error: unknown, fallback: string): string {
  const err = error as {
    code?: string;
    message?: string;
    response?: {
      status?: number;
      data?: {
        detail?: string;
        message?: string;
      };
    };
  };

  const serverMessage = err.response?.data?.detail || err.response?.data?.message;
  if (serverMessage) return serverMessage;

  if (err.response?.status === 401) return '登录状态已失效，请重新登录';
  if (err.response?.status === 403) return '当前账号权限不足';
  if (err.code === 'ERR_NETWORK') return '无法连接后端服务，请确认后端已启动在 8888 端口';
  if (err.message?.includes('timeout')) return '请求超时，请确认后端服务和数据库可用';

  return fallback;
}

export function mockResolve<T>(data: T, delay = 120): Promise<T> {
  return new Promise((resolve) => {
    window.setTimeout(() => resolve(data), delay);
  });
}
