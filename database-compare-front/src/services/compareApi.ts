import api from './api';
import { CompareTaskConfig, ApiResponse } from '@/types';

// 任务进度
export interface TaskProgress {
  taskId: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  currentTable?: string;
  totalTables: number;
  completedTables: number;
  startedAt?: string;
  elapsedTime?: string;
  estimatedRemaining?: string;
  errorMessage?: string;
}

// 任务创建响应
export interface TaskCreated {
  taskId: string;
  status: string;
}

export const compareApi = {
  // 创建并启动比对任务
  startTask: (config: CompareTaskConfig) => 
    api.post<ApiResponse<TaskCreated>>('/compare/start', config),

  // 创建任务（不启动）
  createTask: (config: CompareTaskConfig) =>
    api.post<ApiResponse<TaskCreated>>('/compare/tasks', config),

  // 启动已创建的任务
  startCreatedTask: (taskId: string) =>
    api.post<ApiResponse<TaskCreated>>(`/compare/tasks/${taskId}/start`),

  // 暂停任务
  pauseTask: (taskId: string) => 
    api.post<ApiResponse<null>>(`/compare/${taskId}/pause`),

  // 恢复任务
  resumeTask: (taskId: string) => 
    api.post<ApiResponse<null>>(`/compare/${taskId}/resume`),

  // 停止任务
  stopTask: (taskId: string) => 
    api.post<ApiResponse<null>>(`/compare/${taskId}/stop`),

  // 取消任务
  cancelTask: (taskId: string) =>
    api.post<ApiResponse<null>>(`/compare/tasks/${taskId}/cancel`),

  // 获取任务进度
  getProgress: (taskId: string) =>
    api.get<ApiResponse<TaskProgress>>(`/compare/tasks/${taskId}/progress`),
};
