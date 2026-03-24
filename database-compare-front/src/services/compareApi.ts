import api from './api';
import { CompareTaskConfig } from '@/types';

export const compareApi = {
  startTask: (config: CompareTaskConfig) => api.post<{ taskId: string }>('/compare/start', config),
  pauseTask: (taskId: string) => api.post(`/compare/${taskId}/pause`),
  resumeTask: (taskId: string) => api.post(`/compare/${taskId}/resume`),
  stopTask: (taskId: string) => api.post(`/compare/${taskId}/stop`),
};
