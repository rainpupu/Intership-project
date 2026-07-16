import axios from 'axios';

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
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
