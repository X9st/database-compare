import api from './api';
import { ApiResponse } from '@/types';

export interface HistoryItem {
  task_id: string;
  result_id?: string;
  source_db: {
    id: string;
    name: string;
    db_type: string;
  };
  target_db: {
    id: string;
    name: string;
    db_type: string;
  };
  status: string;
  table_count: number;
  has_diff: boolean;
  structure_diffs_count: number;
  data_diffs_count: number;
  created_at: string;
  duration_seconds?: number;
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

  delete: (task_id: string) =>
    api.delete<ApiResponse<null>>(`/history/${task_id}`),

  batchDelete: (task_ids: string[]) =>
    api.post<ApiResponse<{ deleted: number }>>('/history/batch-delete', { task_ids }),

  cleanup: (before_date?: string, keep_count?: number) =>
    api.post<ApiResponse<{ deleted: number }>>('/history/cleanup', { before_date, keep_count }),
};
