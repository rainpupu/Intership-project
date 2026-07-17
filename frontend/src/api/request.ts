import axios from 'axios';

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  withCredentials: true,
});

request.interceptors.request.use((config) => {
  const rawToken = localStorage.getItem('cattrace_token');
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

export function mockResolve<T>(data: T, delay = 120): Promise<T> {
  return new Promise((resolve) => {
    window.setTimeout(() => resolve(data), delay);
  });
}
