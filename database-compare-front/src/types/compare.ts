export type TableSelectionMode = 'all' | 'include' | 'exclude' | 'mapping';
export type CompareMode = 'full' | 'incremental';

export interface TableSelection {
  mode: TableSelectionMode;
  tables: string[];
}

export interface TableMapping {
  source_table: string;
  target_table: string;
  column_mappings?: ColumnMapping[];
}

export interface ColumnMapping {
  source_column: string;
  target_column: string;
}

export interface TablePrimaryKeyConfig {
  source_table: string;
  primary_keys: string[];
  target_table?: string;
  target_primary_keys?: string[];
}

export interface IgnoreRule {
  id: string;
  name: string;
  rule_type: 'column' | 'dataType' | 'diffType' | 'table';
  pattern: string;
  tables?: string[];
  enabled: boolean;
}

export interface CompareOptions {
  mode: CompareMode;
  resume_from_checkpoint?: boolean;
  incremental_config?: {
    time_column?: string;
    target_time_column?: string;
    start_time?: string;
    end_time?: string;
    batch_column?: string;
    target_batch_column?: string;
    batch_value?: string;
  };
  structure_options: {
    compare_index: boolean;
    compare_constraint: boolean;
    compare_comment: boolean;
  };
  data_options: {
    float_precision: number;
    ignore_case: boolean;
    trim_whitespace: boolean;
    datetime_precision: 'second' | 'millisecond';
    skip_large_fields: boolean;
    page_size: number;
  };
  table_mappings: TableMapping[];
  table_primary_keys?: TablePrimaryKeyConfig[];
  ignore_rules: string[];
}

export interface CompareTaskConfig {
  source_id: string;
  target_id: string;
  table_selection: TableSelection;
  options: CompareOptions;
}

export interface CompareProgress {
  total_tables: number;
  completed_tables: number;
  current_table: string;
  current_phase: 'structure' | 'data';
  percentage: number;
  start_time: string;
  elapsed_seconds: number;
  estimated_remaining_seconds?: number;
}
