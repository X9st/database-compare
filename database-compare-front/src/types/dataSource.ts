export type DatabaseType = 'mysql' | 'oracle' | 'dm' | 'inceptor' | 'excel' | 'dbf';
export type FileSourceMode = 'single_file' | 'remote_dataset';

export interface SftpConfig {
  transport?: 'sftp';
  host: string;
  port: number;
  username: string;
  password?: string;
  password_encrypted?: string;
  base_dir: string;
}

export interface DatasetTableEntry {
  storage_key: string;
  original_name?: string;
  file_type?: 'xlsx' | 'xls' | 'dbf';
  sheet_name?: string;
}

export interface DatasetSnapshot {
  dataset_root: string;
  table_index: Record<string, DatasetTableEntry>;
  file_count: number;
  table_count: number;
  failed_files: Array<{ file_name: string; error: string }>;
  last_refresh_at: string;
}

export interface DataSourceExtraConfig {
  mode?: FileSourceMode;
  storage_key?: string;
  original_name?: string;
  file_type?: 'xlsx' | 'xls' | 'dbf';
  file_id?: string;
  file_size?: number;
  sheet_mode?: 'all';
  header_row?: number;
  sftp?: SftpConfig;
  snapshot?: DatasetSnapshot;
}

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
  extra_config?: DataSourceExtraConfig;
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
  host?: string;
  port?: number;
  database?: string;
  schema?: string;
  username?: string;
  password?: string;
  charset?: string;
  timeout?: number;
  extra_config?: DataSourceExtraConfig;
}

export interface FileUploadResult {
  file_id: string;
  storage_key: string;
  original_name: string;
  file_type: 'xlsx' | 'xls' | 'dbf';
  file_size: number;
}

export interface CreateRemoteDatasetDto {
  name: string;
  group_id?: string;
  db_type: 'excel' | 'dbf';
  database?: string;
  charset?: string;
  timeout?: number;
  extra_config: {
    mode: 'remote_dataset';
    file_type?: 'xlsx' | 'xls' | 'dbf';
    sftp: SftpConfig;
  };
}

export interface RemoteDatasetRefreshResult {
  datasource_id: string;
  file_count: number;
  table_count: number;
  failed_files: Array<{ file_name: string; error: string }>;
  last_refresh_at: string;
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
