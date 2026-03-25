import { DataSource } from './dataSource';

export type StructureDiffType =
  | 'table_missing_in_target'
  | 'table_extra_in_target'
  | 'column_missing'
  | 'column_extra'
  | 'column_type_diff'
  | 'column_length_diff'
  | 'column_nullable_diff'
  | 'column_default_diff'
  | 'index_diff'
  | 'constraint_diff'
  | 'comment_diff';

export type DataDiffType =
  | 'row_count_diff'
  | 'row_missing_in_target'
  | 'row_extra_in_target'
  | 'value_diff'
  | 'null_diff';

export interface StructureDiffItem {
  id: string;
  table_name: string;
  diff_type: StructureDiffType;
  field_name?: string;
  source_value: string | null;
  target_value: string | null;
  diff_detail: string;
}

export interface DataDiffItem {
  id: string;
  table_name: string;
  primary_key: Record<string, any>;
  diff_type: DataDiffType;
  diff_columns: string[];
  source_values?: Record<string, any>;
  target_values?: Record<string, any>;
}

export interface TableCompareResult {
  table_name: string;
  structure_match: boolean;
  data_match: boolean;
  source_row_count: number;
  target_row_count: number;
  structure_diffs: StructureDiffItem[];
  data_diffs: DataDiffItem[];
  compare_time_ms: number;
}

export interface CompareResultSummary {
  total_tables: number;
  structure_match_tables: number;
  structure_diff_tables: number;
  data_match_tables: number;
  data_diff_tables: number;
  total_structure_diffs: number;
  total_data_diffs: number;
}

export interface CompareResult {
  task_id: string;
  status: 'completed' | 'partial' | 'failed';
  source_db: DataSource;
  target_db: DataSource;
  start_time: string;
  end_time: string;
  duration_seconds: number;
  summary: CompareResultSummary;
  table_results: TableCompareResult[];
  error_message?: string;
}
