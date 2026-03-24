import axios from 'axios';
import { message } from 'antd';

const API_BASE_URL = 'http://localhost:18765/api/v1';

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
    const errorMsg = error.response?.data?.message || '请求失败，请稍后重试';
    message.error(errorMsg);
    return Promise.reject(error);
  }
);

export default api;
