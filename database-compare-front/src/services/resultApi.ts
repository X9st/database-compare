import api from './api';
import { ApiResponse } from '@/types';

// 比对结果汇总
export interface CompareResultSummary {
  id: string;
  taskId: string;
  totalTables: number;
  structureSameCount: number;
  structureDiffCount: number;
  dataSameCount: number;
  dataDiffCount: number;
  elapsedTime: string;
  createdAt: string;
}

// 结构差异
export interface StructureDiff {
  id: string;
  tableName: string;
  diffType: string;
  fieldName?: string;
  sourceValue?: string;
  targetValue?: string;
  diffDetail: string;
}

// 数据差异
export interface DataDiff {
  id: string;
  tableName: string;
  primaryKey: Record<string, any>;
  diffType: string;
  diffColumns: string[];
  sourceValues?: Record<string, any>;
  targetValues?: Record<string, any>;
}

// 单表详情
export interface TableCompareDetail {
  tableName: string;
  structureStatus: 'same' | 'diff';
  dataStatus: 'same' | 'diff';
  structureDiffs: StructureDiff[];
  dataDiffCount: number;
  sourceRowCount: number;
  targetRowCount: number;
}

// 分页响应
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

// 导出请求
export interface ExportRequest {
  format: 'excel' | 'html' | 'txt';
  includeSummary?: boolean;
  includeStructureDiff?: boolean;
  includeDataDiff?: boolean;
  tables?: string[];
}

// 导出响应
export interface ExportResult {
  filePath: string;
  fileName: string;
  fileSize: number;
  downloadUrl: string;
}

export const resultApi = {
  // 获取比对结果汇总
  getResult: (resultId: string) =>
    api.get<ApiResponse<CompareResultSummary>>(`/compare/results/${resultId}`),

  // 获取结构差异列表（分页）
  getStructureDiffs: (
    resultId: string,
    params?: { table_name?: string; diff_type?: string; page?: number; page_size?: number }
  ) =>
    api.get<PageResponse<StructureDiff>>(`/compare/results/${resultId}/structure-diffs`, { params }),

  // 获取数据差异列表（分页）
  getDataDiffs: (
    resultId: string,
    params?: { table_name?: string; diff_type?: string; page?: number; page_size?: number }
  ) =>
    api.get<PageResponse<DataDiff>>(`/compare/results/${resultId}/data-diffs`, { params }),

  // 获取单表比对详情
  getTableDetail: (resultId: string, tableName: string) =>
    api.get<ApiResponse<TableCompareDetail>>(`/compare/results/${resultId}/tables/${tableName}`),

  // 导出比对报告
  exportReport: (resultId: string, request: ExportRequest) =>
    api.post<ApiResponse<ExportResult>>(`/compare/results/${resultId}/export`, request),
};
