import axios from 'axios';
import { message } from 'antd';

export const API_BASE_URL = 'http://localhost:18765/api/v1';

export const resolveApiUrl = (path: string): string => {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  if (path.startsWith('/')) {
    return `http://localhost:18765${path}`;
  }
  return `${API_BASE_URL}/${path}`;
};

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    // @ts-ignore
    config.metadata = { startTime: Date.now() };
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (!error.response) {
      const networkMsg = `网络请求失败: ${error.message || '请检查后端服务与跨域配置'}`;
      message.error(networkMsg);
      return Promise.reject(error);
    }
    const errorMsg =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      '请求失败，请稍后重试';
    message.error(errorMsg);
    return Promise.reject(error);
  }
);

export default api;
