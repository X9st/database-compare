import { create } from 'zustand';
import { compareApi } from '@/services/compareApi';
import { CompareTaskConfig, TableSelection, CompareOptions, CompareProgress } from '@/types';

interface CompareState {
  current_task: CompareTaskConfig | null;
  task_status: 'idle' | 'running' | 'paused' | 'completed' | 'error';
  progress: CompareProgress | null;
  task_id: string | null;
  result_id: string | null;

  setSourceDb: (id: string) => void;
  setTargetDb: (id: string) => void;
  setTables: (tables: TableSelection) => void;
  setCompareOptions: (options: CompareOptions) => void;

  startCompare: () => Promise<string>;
  resetTask: () => void;
}

export const useCompareStore = create<CompareState>((set, get) => ({
  current_task: {
    source_id: '',
    target_id: '',
    table_selection: { mode: 'all', tables: [] },
    options: {
      mode: 'full',
      structure_options: { compare_index: true, compare_constraint: true, compare_comment: true },
      data_options: { float_precision: 6, ignore_case: false, trim_whitespace: true, datetime_precision: 'second', skip_large_fields: false, page_size: 1000 },
      table_mappings: [],
      ignore_rules: []
    }
  },
  task_status: 'idle',
  progress: null,
  task_id: null,
  result_id: null,

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
      const response = await compareApi.startTask(current_task);
      const task_id = response.data?.data?.task_id;
      if (!task_id) {
        throw new Error('Failed to get task ID');
      }
      set({ task_id, result_id: null });
      return task_id;
    } catch (e) {
      set({ task_status: 'error' });
      throw e;
    }
  },
  resetTask: () => set({ task_status: 'idle', progress: null, task_id: null, result_id: null })
}));
