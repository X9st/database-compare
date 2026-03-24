// API 服务统一导出
export { default as api } from './api';
export { dataSourceApi, type DataSourceGroup, type CreateGroupDto } from './dataSourceApi';
export { compareApi, type TaskProgress, type TaskCreated } from './compareApi';
export { 
  resultApi, 
  type CompareResultSummary, 
  type StructureDiff, 
  type DataDiff, 
  type TableCompareDetail,
  type ExportRequest,
  type ExportResult,
  type PageInfo,
  type PageResponse,
} from './resultApi';
export { historyApi, type HistoryItem, type HistoryQuery } from './historyApi';
export { 
  settingsApi, 
  type IgnoreRule, 
  type CreateIgnoreRuleRequest, 
  type SystemSettings, 
  type UpdateSystemSettingsRequest 
} from './settingsApi';
