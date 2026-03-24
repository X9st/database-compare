import api from './api';
import { ApiResponse } from '@/types';

export interface IgnoreRule {
  id: string;
  name: string;
  ruleType: 'column' | 'dataType' | 'diffType' | 'table';
  pattern: string;
  tables?: string[];
  enabled: boolean;
  createdAt: string;
}

export interface CreateIgnoreRuleRequest {
  name: string;
  rule_type: string;
  pattern: string;
  tables?: string[];
  enabled?: boolean;
}

export interface SystemSettings {
  defaultThreadCount: number;
  queryTimeout: number;
  compareTimeout: number;
  enableCheckpoint: boolean;
  maxDiffDisplay: number;
  historyRetentionDays: number;
}

export interface UpdateSystemSettingsRequest {
  default_thread_count?: number;
  query_timeout?: number;
  compare_timeout?: number;
  enable_checkpoint?: boolean;
  max_diff_display?: number;
  history_retention_days?: number;
}

export const settingsApi = {
  // 忽略规则
  getIgnoreRules: () => 
    api.get<ApiResponse<IgnoreRule[]>>('/settings/ignore-rules'),
  
  createIgnoreRule: (data: CreateIgnoreRuleRequest) =>
    api.post<ApiResponse<IgnoreRule>>('/settings/ignore-rules', data),
  
  updateIgnoreRule: (id: string, data: Partial<CreateIgnoreRuleRequest>) =>
    api.put<ApiResponse<IgnoreRule>>(`/settings/ignore-rules/${id}`, data),
  
  deleteIgnoreRule: (id: string) =>
    api.delete<ApiResponse<null>>(`/settings/ignore-rules/${id}`),
  
  toggleIgnoreRule: (id: string, enabled: boolean) =>
    api.put<ApiResponse<null>>(`/settings/ignore-rules/${id}/toggle`, { enabled }),

  // 系统设置
  getSystemSettings: () =>
    api.get<ApiResponse<SystemSettings>>('/settings/system'),
  
  updateSystemSettings: (data: UpdateSystemSettingsRequest) =>
    api.put<ApiResponse<SystemSettings>>('/settings/system', data),
};
