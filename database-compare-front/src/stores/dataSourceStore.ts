import { create } from 'zustand';
import { dataSourceApi } from '@/services/dataSourceApi';
import { DataSource, DataSourceGroup, CreateDataSourceDto, TestConnectionResult } from '@/types';

interface DataSourceState {
  dataSources: DataSource[];
  groups: DataSourceGroup[];
  loading: boolean;
  
  fetchDataSources: () => Promise<void>;
  addDataSource: (data: CreateDataSourceDto) => Promise<void>;
  updateDataSource: (id: string, data: Partial<CreateDataSourceDto>) => Promise<void>;
  deleteDataSource: (id: string) => Promise<void>;
  testConnection: (id: string) => Promise<TestConnectionResult>;
  
  fetchGroups: () => Promise<void>;
  addGroup: (name: string) => Promise<void>;
  deleteGroup: (id: string) => Promise<void>;
}

export const useDataSourceStore = create<DataSourceState>((set) => ({
  dataSources: [],  // 初始为空数组，从后端加载
  groups: [],
  loading: false,

  fetchDataSources: async () => {
    set({ loading: true });
    try {
      const response = await dataSourceApi.getList();
      // 后端返回格式: { code: 0, message: 'success', data: [...] }
      const data = response.data?.data || [];
      set({ dataSources: Array.isArray(data) ? data : [] });
    } catch (e) {
      // API 请求失败时保持原有数据
      console.error('Failed to fetch datasources:', e);
      throw e;
    } finally {
      set({ loading: false });
    }
  },

  addDataSource: async (data) => {
    const response = await dataSourceApi.create(data);
    const created = response.data?.data;
    if (created) {
      set((state) => ({
        dataSources: [created, ...state.dataSources.filter((item) => item.id !== created.id)],
      }));
    }
  },

  updateDataSource: async (id, data) => {
    const response = await dataSourceApi.update(id, data);
    const updated = response.data?.data;
    if (updated) {
      set((state) => ({
        dataSources: state.dataSources.map((ds) => (ds.id === id ? updated : ds))
      }));
    }
  },

  deleteDataSource: async (id) => {
    await dataSourceApi.delete(id);
    set((state) => ({
      dataSources: state.dataSources.filter((ds) => ds.id !== id),
    }));
  },

  testConnection: async (id) => {
    try {
      const response = await dataSourceApi.testConnection(id);
      // 后端返回格式: { code: 0, message: 'success', data: {...} }
      return response.data?.data || { success: false, message: '请求失败' };
    } catch (e) {
      return { success: false, message: '连接测试失败' };
    }
  },

  fetchGroups: async () => {},
  addGroup: async (_name) => {},
  deleteGroup: async (_id) => {},
}));
