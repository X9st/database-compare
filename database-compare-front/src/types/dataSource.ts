export type DatabaseType = 'mysql' | 'oracle' | 'sqlserver' | 'postgresql' | 'dm' | 'inceptor';

// 通用 API 响应格式
export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export interface DataSource {
  id: string;
  name: string;
  group_id?: string;
  group_name?: string;
  db_type: DatabaseType;
  host: string;
  port: number;
  database: string;
  schema?: string;
  username: string;
  charset: string;
  timeout: number;
  created_at: string;
  updated_at: string;
}

export interface DataSourceGroup {
  id: string;
  name: string;
  count: number;
  sort_order: number;
}

export interface CreateDataSourceDto {
  name: string;
  group_id?: string;
  db_type: DatabaseType;
  host: string;
  port: number;
  database: string;
  schema?: string;
  username: string;
  password?: string;
  charset?: string;
  timeout?: number;
}

export interface TestConnectionResult {
  success: boolean;
  message: string;
  latency?: number;
  version?: string;
}

export interface TableInfo {
  name: string;
  schema?: string;
  comment?: string;
  row_count?: number;
}
