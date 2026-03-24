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
  tableName: string;
  diffType: StructureDiffType;
  fieldName?: string;
  sourceValue: string | null;
  targetValue: string | null;
  diffDetail: string;
}

export interface DataDiffItem {
  id: string;
  tableName: string;
  primaryKey: Record<string, any>;
  diffType: DataDiffType;
  diffColumns: string[];
  sourceValues?: Record<string, any>;
  targetValues?: Record<string, any>;
}

export interface TableCompareResult {
  tableName: string;
  structureMatch: boolean;
  dataMatch: boolean;
  sourceRowCount: number;
  targetRowCount: number;
  structureDiffs: StructureDiffItem[];
  dataDiffs: DataDiffItem[];
  compareTime: number;
}

export interface CompareResultSummary {
  totalTables: number;
  structureMatchTables: number;
  structureDiffTables: number;
  dataMatchTables: number;
  dataDiffTables: number;
  totalStructureDiffs: number;
  totalDataDiffs: number;
}

export interface CompareResult {
  taskId: string;
  status: 'completed' | 'partial' | 'failed';
  sourceDb: DataSource;
  targetDb: DataSource;
  startTime: string;
  endTime: string;
  duration: number;
  summary: CompareResultSummary;
  tableResults: TableCompareResult[];
  errorMessage?: string;
}
