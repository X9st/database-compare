import api from './api';
import { ApiResponse } from '@/types';

export interface CompareResultSummary {
  result_id: string;
  task_id: string;
  status: string;
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
  start_time: string;
  end_time?: string;
  duration_seconds?: number;
  summary: {
    total_tables: number;
    structure_match_tables: number;
    structure_diff_tables: number;
    data_match_tables: number;
    data_diff_tables: number;
    total_structure_diffs: number;
    total_data_diffs: number;
  };
}

export interface StructureDiff {
  id: string;
  table_name: string;
  diff_type: string;
  field_name?: string;
  source_value?: string;
  target_value?: string;
  diff_detail?: string;
}

export interface DataDiff {
  id: string;
  table_name: string;
  primary_key: Record<string, any>;
  diff_type: string;
  diff_columns: string[];
  source_values?: Record<string, any>;
  target_values?: Record<string, any>;
}

export interface TableCompareDetail {
  table_name: string;
  structure_match: boolean;
  data_match: boolean;
  source_row_count: number;
  target_row_count: number;
  structure_diffs_count: number;
  data_diffs_count: number;
  compare_time_ms: number;
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

export interface ExportRequest {
  format: 'excel' | 'html' | 'txt';
  options?: {
    include_structure_diffs?: boolean;
    include_data_diffs?: boolean;
    max_data_diffs?: number;
    tables?: string[];
  };
}

export interface ExportResult {
  file_path: string;
  file_name: string;
  file_size: number;
  download_url: string;
}

export const resultApi = {
  // 获取比对结果汇总
  getResult: (result_id: string) =>
    api.get<ApiResponse<CompareResultSummary>>(`/compare/results/${result_id}`),

  // 获取结构差异列表（分页）
  getStructureDiffs: (
    result_id: string,
    params?: { table_name?: string; diff_type?: string; page?: number; page_size?: number }
  ) =>
    api.get<PageResponse<StructureDiff>>(`/compare/results/${result_id}/structure-diffs`, { params }),

  // 获取数据差异列表（分页）
  getDataDiffs: (
    result_id: string,
    params?: { table_name?: string; diff_type?: string; page?: number; page_size?: number }
  ) =>
    api.get<PageResponse<DataDiff>>(`/compare/results/${result_id}/data-diffs`, { params }),

  // 获取单表比对详情
  getTableDetail: (result_id: string, table_name: string) =>
    api.get<ApiResponse<TableCompareDetail>>(`/compare/results/${result_id}/tables/${table_name}`),

  // 导出比对报告
  exportReport: (result_id: string, request: ExportRequest) =>
    api.post<ApiResponse<ExportResult>>(`/compare/results/${result_id}/export`, request),
};
