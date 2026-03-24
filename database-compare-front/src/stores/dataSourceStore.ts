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

export const useDataSourceStore = create<DataSourceState>((set, get) => ({
  dataSources: [
    // Mock data for initial UI testing
    {
      id: '1',
      name: '生产环境-MySQL',
      dbType: 'mysql',
      host: '192.168.1.100',
      port: 3306,
      database: 'prod_db',
      username: 'root',
      charset: 'UTF-8',
      timeout: 30,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
  ],
  groups: [],
  loading: false,

  fetchDataSources: async () => {
    set({ loading: true });
    try {
      const response = await dataSourceApi.getList();
      set({ dataSources: response.data });
    } catch (e) {
      // Ignore for mock
    } finally {
      set({ loading: false });
    }
  },

  addDataSource: async (data) => {
    try {
      await dataSourceApi.create(data);
      await get().fetchDataSources();
    } catch (e) {
      // Mock fallback
      set((state) => ({
        dataSources: [...state.dataSources, { ...data, id: Date.now().toString(), createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() } as DataSource]
      }));
    }
  },

  updateDataSource: async (id, data) => {
    try {
      await dataSourceApi.update(id, data);
      await get().fetchDataSources();
    } catch (e) {
      // Mock fallback
      set((state) => ({
        dataSources: state.dataSources.map(ds => ds.id === id ? { ...ds, ...data } : ds)
      }));
    }
  },

  deleteDataSource: async (id) => {
    try {
      await dataSourceApi.delete(id);
    } catch (e) {
      // Mock fallback
    }
    set((state) => ({
      dataSources: state.dataSources.filter((ds) => ds.id !== id),
    }));
  },

  testConnection: async (id) => {
    try {
      const response = await dataSourceApi.testConnection(id);
      return response.data;
    } catch (e) {
      return { success: true, message: 'Mock connection success', latency: 12 };
    }
  },

  fetchGroups: async () => {},
  addGroup: async (name) => {},
  deleteGroup: async (id) => {},
}));
