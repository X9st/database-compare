import api from './api';
import { CompareTaskConfig, ApiResponse } from '@/types';

export interface TaskStatusResponse {
  task_id: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  progress: {
    total_tables: number;
    completed_tables: number;
    current_table?: string;
    current_phase?: 'structure' | 'data';
    percentage: number;
    start_time?: string;
    elapsed_seconds: number;
    estimated_remaining_seconds?: number;
  };
  error_message?: string;
  result_id?: string;
}

export interface TaskCreated {
  task_id: string;
  status: string;
  created_at?: string;
  resume_from_task_id?: string | null;
}

export const compareApi = {
  // 创建并启动比对任务
  startTask: (config: CompareTaskConfig) =>
    api.post<ApiResponse<TaskCreated>>('/compare/start', config),

  // 创建任务（不启动）
  createTask: (config: CompareTaskConfig) =>
    api.post<ApiResponse<TaskCreated>>('/compare/tasks', config),

  // 启动已创建的任务
  startCreatedTask: (task_id: string) =>
    api.post<ApiResponse<TaskCreated>>(`/compare/tasks/${task_id}/start`),

  // 暂停任务
  pauseTask: (task_id: string) =>
    api.post<ApiResponse<null>>(`/compare/${task_id}/pause`),

  // 恢复任务
  resumeTask: (task_id: string) =>
    api.post<ApiResponse<null>>(`/compare/${task_id}/resume`),

  // 停止任务
  stopTask: (task_id: string) =>
    api.post<ApiResponse<null>>(`/compare/${task_id}/stop`),

  // 取消任务
  cancelTask: (task_id: string) =>
    api.post<ApiResponse<null>>(`/compare/tasks/${task_id}/cancel`),

  // 获取任务进度
  getProgress: (task_id: string) =>
    api.get<ApiResponse<TaskStatusResponse>>(`/compare/tasks/${task_id}/progress`),
};
