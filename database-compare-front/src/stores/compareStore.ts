import { create } from 'zustand';
import { compareApi, TaskCreated } from '@/services/compareApi';
import { CompareTaskConfig, TableSelection, CompareOptions, CompareProgress } from '@/types';

interface CompareState {
  current_task: CompareTaskConfig | null;
  task_status: 'idle' | 'running' | 'paused' | 'completed' | 'error';
  progress: CompareProgress | null;
  task_id: string | null;
  result_id: string | null;
  resume_from_task_id: string | null;

  setSourceDb: (id: string) => void;
  setTargetDb: (id: string) => void;
  setTables: (tables: TableSelection) => void;
  setCompareOptions: (options: CompareOptions) => void;

  startCompare: () => Promise<TaskCreated>;
  resetTask: () => void;
}

export const useCompareStore = create<CompareState>((set, get) => ({
  current_task: {
    source_id: '',
    target_id: '',
    table_selection: { mode: 'all', tables: [] },
    options: {
      mode: 'full',
      resume_from_checkpoint: true,
      structure_options: { compare_index: true, compare_constraint: true, compare_comment: true },
      data_options: { float_precision: 6, ignore_case: false, trim_whitespace: true, datetime_precision: 'second', skip_large_fields: false, page_size: 1000 },
      table_mappings: [],
      table_primary_keys: [],
      ignore_rules: []
    }
  },
  task_status: 'idle',
  progress: null,
  task_id: null,
  result_id: null,
  resume_from_task_id: null,

  setSourceDb: (id) => set((state) => ({ current_task: { ...state.current_task!, source_id: id } })),
  setTargetDb: (id) => set((state) => ({ current_task: { ...state.current_task!, target_id: id } })),
  setTables: (tables) => set((state) => ({ current_task: { ...state.current_task!, table_selection: tables } })),
  setCompareOptions: (options) => set((state) => ({ current_task: { ...state.current_task!, options } })),

  startCompare: async () => {
    const { current_task } = get();
    if (!current_task) {
      throw new Error('No task config');
    }
    try {
      set({ task_status: 'running' });
      const response = await compareApi.startTask(normalizeTaskConfig(current_task));
      const payload = response.data?.data;
      const task_id = payload?.task_id;
      if (!task_id) {
        throw new Error('Failed to get task ID');
      }
      set({ task_id, result_id: null, resume_from_task_id: payload?.resume_from_task_id || null });
      return payload;
    } catch (e) {
      set({ task_status: 'error' });
      throw e;
    }
  },
  resetTask: () => set({ task_status: 'idle', progress: null, task_id: null, result_id: null, resume_from_task_id: null })
}));

function normalizeTaskConfig(config: CompareTaskConfig): CompareTaskConfig {
  const next = JSON.parse(JSON.stringify(config)) as CompareTaskConfig;
  const options = next.options;

  options.table_mappings = (options.table_mappings || [])
    .filter((item) => item.source_table && item.target_table)
    .map((item) => ({
      source_table: item.source_table,
      target_table: item.target_table,
      column_mappings: (item.column_mappings || [])
        .filter((mapping) => mapping.source_column && mapping.target_column),
    }));

  options.table_primary_keys = (options.table_primary_keys || [])
    .filter((item) => item.source_table && (item.primary_keys || []).length > 0)
    .map((item) => ({
      source_table: item.source_table,
      primary_keys: item.primary_keys.filter(Boolean),
      target_table: item.target_table || undefined,
      target_primary_keys: (item.target_primary_keys || []).filter(Boolean),
    }));

  if (options.mode !== 'incremental') {
    delete options.incremental_config;
  } else {
    const inc = options.incremental_config || {};
    options.incremental_config = {
      time_column: inc.time_column || undefined,
      target_time_column: inc.target_time_column || undefined,
      start_time: inc.start_time || undefined,
      end_time: inc.end_time || undefined,
      batch_column: inc.batch_column || undefined,
      target_batch_column: inc.target_batch_column || undefined,
      batch_value: inc.batch_value || undefined,
    };
  }

  if (typeof options.resume_from_checkpoint !== 'boolean') {
    options.resume_from_checkpoint = true;
  }

  return next;
}
