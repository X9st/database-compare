import api from './api';
import { ApiResponse } from '@/types';

export interface HistoryItem {
  id: string;
  sourceId: string;
  sourceName?: string;
  targetId: string;
  targetName?: string;
  status: string;
  startedAt: string;
  completedAt?: string;
  errorMessage?: string;
}

export interface PageInfo {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface PageResponse<T> {
  code: number;
  message: string;
  data: T[];
  page_info: PageInfo;
}

export interface HistoryQuery {
  source_id?: string;
  target_id?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  keyword?: string;
  page?: number;
  page_size?: number;
}

export const historyApi = {
  getList: (params?: HistoryQuery) => 
    api.get<PageResponse<HistoryItem>>('/history', { params }),
  
  delete: (taskId: string) => 
    api.delete<ApiResponse<null>>(`/history/${taskId}`),
  
  batchDelete: (taskIds: string[]) =>
    api.post<ApiResponse<{ deleted: number }>>('/history/batch-delete', { task_ids: taskIds }),
  
  cleanup: (beforeDate?: string, keepCount?: number) =>
    api.post<ApiResponse<{ deleted: number }>>('/history/cleanup', { before_date: beforeDate, keep_count: keepCount }),
};
