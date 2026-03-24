export type DatabaseType = 'mysql' | 'oracle' | 'sqlserver' | 'postgresql' | 'dm' | 'inceptor';

export interface DataSource {
  id: string;
  name: string;
  groupId?: string;
  groupName?: string;
  dbType: DatabaseType;
  host: string;
  port: number;
  database: string;
  schema?: string;
  username: string;
  charset: string;
  timeout: number;
  createdAt: string;
  updatedAt: string;
}

export interface DataSourceGroup {
  id: string;
  name: string;
  count: number;
}

export interface CreateDataSourceDto {
  name: string;
  groupId?: string;
  dbType: DatabaseType;
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
