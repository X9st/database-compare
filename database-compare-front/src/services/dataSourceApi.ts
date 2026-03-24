import api from './api';
import { DataSource, CreateDataSourceDto, TestConnectionResult, ApiResponse } from '@/types';

// 数据源分组
export interface DataSourceGroup {
  id: string;
  name: string;
  description?: string;
  createdAt: string;
}

export interface CreateGroupDto {
  name: string;
  description?: string;
}

export const dataSourceApi = {
  // ============ 数据源接口 ============
  getList: (params?: { group_id?: string; keyword?: string; db_type?: string }) => 
    api.get<ApiResponse<DataSource[]>>('/datasources', { params }),
  
  getById: (id: string) => 
    api.get<ApiResponse<DataSource>>(`/datasources/${id}`),
  
  create: (data: CreateDataSourceDto) => 
    api.post<ApiResponse<DataSource>>('/datasources', data),
  
  update: (id: string, data: Partial<CreateDataSourceDto>) => 
    api.put<ApiResponse<DataSource>>(`/datasources/${id}`, data),
  
  delete: (id: string) => 
    api.delete<ApiResponse<null>>(`/datasources/${id}`),
  
  testConnection: (id: string) => 
    api.post<ApiResponse<TestConnectionResult>>(`/datasources/${id}/test`),
  
  testConnectionDirect: (data: CreateDataSourceDto) =>
    api.post<ApiResponse<TestConnectionResult>>(`/datasources/test`, data),
  
  getTables: (id: string, schema?: string) => 
    api.get<ApiResponse<string[]>>(`/datasources/${id}/tables`, { params: { schema } }),
  
  getTableSchema: (id: string, tableName: string) =>
    api.get<ApiResponse<any>>(`/datasources/${id}/tables/${tableName}/schema`),

  // ============ 分组接口 ============
  getGroups: () =>
    api.get<ApiResponse<DataSourceGroup[]>>('/datasource-groups'),

  createGroup: (data: CreateGroupDto) =>
    api.post<ApiResponse<DataSourceGroup>>('/datasource-groups', data),

  updateGroup: (id: string, data: Partial<CreateGroupDto>) =>
    api.put<ApiResponse<DataSourceGroup>>(`/datasource-groups/${id}`, data),

  deleteGroup: (id: string) =>
    api.delete<ApiResponse<null>>(`/datasource-groups/${id}`),
};
