import api from './api';
import { ApiResponse } from '@/types';

export interface IgnoreRule {
  id: string;
  name: string;
  rule_type: 'column' | 'dataType' | 'diffType' | 'table';
  pattern: string;
  tables?: string[];
  enabled: boolean;
  created_at: string;
}

export interface CreateIgnoreRuleRequest {
  name: string;
  rule_type: string;
  pattern: string;
  tables?: string[];
  enabled?: boolean;
}

export interface SystemSettings {
  compare_thread_count: number;
  db_query_timeout: number;
  compare_timeout: number;
  history_retention_days: number;
  history_max_count: number;
  default_page_size: number;
  max_diff_display: number;
  auto_cleanup_enabled: boolean;
}

export interface UpdateSystemSettingsRequest {
  compare_thread_count?: number;
  db_query_timeout?: number;
  compare_timeout?: number;
  history_retention_days?: number;
  history_max_count?: number;
  default_page_size?: number;
  max_diff_display?: number;
  auto_cleanup_enabled?: boolean;
}

export interface ExportConfigRequest {
  include_datasources?: boolean;
  include_templates?: boolean;
  include_rules?: boolean;
  include_system_settings?: boolean;
}

export interface CompareTemplateConfig {
  source_id?: string;
  target_id?: string;
  table_selection?: Record<string, any>;
  options?: Record<string, any>;
}

export interface CompareTemplate {
  id: string;
  name: string;
  description?: string;
  config: CompareTemplateConfig;
  created_at: string;
  updated_at: string;
}

export interface CreateTemplateRequest {
  name: string;
  description?: string;
  config: CompareTemplateConfig;
}

export interface ExportConfigResult {
  file_path: string;
  file_name: string;
  file_size: number;
  download_url: string;
}

export interface ImportConfigResult {
  datasource_groups_imported: number;
  datasources_imported: number;
  templates_imported: number;
  rules_imported: number;
  system_settings_imported: number;
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

  // 模板
  getTemplates: () =>
    api.get<ApiResponse<CompareTemplate[]>>('/settings/templates'),

  createTemplate: (data: CreateTemplateRequest) =>
    api.post<ApiResponse<CompareTemplate>>('/settings/templates', data),

  updateTemplate: (id: string, data: Partial<CreateTemplateRequest>) =>
    api.put<ApiResponse<CompareTemplate>>(`/settings/templates/${id}`, data),

  deleteTemplate: (id: string) =>
    api.delete<ApiResponse<null>>(`/settings/templates/${id}`),

  createTaskFromTemplate: (id: string, override?: Record<string, any>) =>
    api.post<ApiResponse<{ task_id: string; status: string; created_at: string }>>(`/settings/templates/${id}/create-task`, { override }),

  // 系统设置
  getSystemSettings: () =>
    api.get<ApiResponse<SystemSettings>>('/settings/system'),

  updateSystemSettings: (data: UpdateSystemSettingsRequest) =>
    api.put<ApiResponse<SystemSettings>>('/settings/system', data),

  // 配置导入导出
  exportConfig: (data: ExportConfigRequest) =>
    api.post<ApiResponse<ExportConfigResult>>('/settings/export', data),

  importConfig: (file: File) => {
    const formData = new FormData();
    formData.append('config_file', file);
    return api.post<ApiResponse<ImportConfigResult>>('/settings/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};
