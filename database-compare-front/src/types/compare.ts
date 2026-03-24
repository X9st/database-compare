export type TableSelectionMode = 'all' | 'include' | 'exclude';
export type CompareMode = 'full' | 'incremental';

export interface TableSelection {
  mode: TableSelectionMode;
  tables: string[];
}

export interface TableMapping {
  sourceTable: string;
  targetTable: string;
  columnMappings?: ColumnMapping[];
}

export interface ColumnMapping {
  sourceColumn: string;
  targetColumn: string;
}

export interface IgnoreRule {
  id: string;
  name: string;
  type: 'column' | 'dataType' | 'diffType' | 'table';
  pattern: string;
  tables?: string[];
  enabled: boolean;
}

export interface CompareOptions {
  mode: CompareMode;
  incrementalConfig?: {
    timeColumn: string;
    startTime: string;
    endTime?: string;
  };
  structureOptions: {
    compareIndex: boolean;
    compareConstraint: boolean;
    compareComment: boolean;
  };
  dataOptions: {
    floatPrecision: number;
    ignoreCase: boolean;
    trimWhitespace: boolean;
    dateTimePrecision: 'second' | 'millisecond';
    skipLargeFields: boolean;
    pageSize: number;
  };
  tableMappings: TableMapping[];
  ignoreRules: string[];
}

export interface CompareTaskConfig {
  sourceId: string;
  targetId: string;
  tableSelection: TableSelection;
  options: CompareOptions;
}

export interface CompareProgress {
  totalTables: number;
  completedTables: number;
  currentTable: string;
  currentPhase: 'structure' | 'data';
  percentage: number;
  startTime: number;
  elapsedTime: number;
  estimatedRemaining?: number;
}
