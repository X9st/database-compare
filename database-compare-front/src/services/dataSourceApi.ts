import api from './api';
import { DataSource, CreateDataSourceDto, TestConnectionResult } from '@/types';

export const dataSourceApi = {
  getList: () => api.get<DataSource[]>('/datasources'),
  getById: (id: string) => api.get<DataSource>(`/datasources/${id}`),
  create: (data: CreateDataSourceDto) => api.post<DataSource>('/datasources', data),
  update: (id: string, data: Partial<CreateDataSourceDto>) => 
    api.put<DataSource>(`/datasources/${id}`, data),
  delete: (id: string) => api.delete(`/datasources/${id}`),
  testConnection: (id: string) => 
    api.post<TestConnectionResult>(`/datasources/${id}/test`),
  testConnectionDirect: (data: CreateDataSourceDto) =>
    api.post<TestConnectionResult>(`/datasources/test`, data),
  getTables: (id: string, schema?: string) => 
    api.get<string[]>(`/datasources/${id}/tables`, { params: { schema } }),
  getTableSchema: (id: string, tableName: string) =>
    api.get(`/datasources/${id}/tables/${tableName}/schema`),
};
