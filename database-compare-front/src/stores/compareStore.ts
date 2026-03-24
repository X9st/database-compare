import { create } from 'zustand';
import { compareApi } from '@/services/compareApi';
import { CompareTaskConfig, TableSelection, CompareOptions, CompareProgress } from '@/types';

interface CompareState {
  currentTask: CompareTaskConfig | null;
  taskStatus: 'idle' | 'running' | 'paused' | 'completed' | 'error';
  progress: CompareProgress | null;
  taskId: string | null;

  setSourceDb: (id: string) => void;
  setTargetDb: (id: string) => void;
  setTables: (tables: TableSelection) => void;
  setCompareOptions: (options: CompareOptions) => void;

  startCompare: () => Promise<string>;
  resetTask: () => void;
}

export const useCompareStore = create<CompareState>((set, get) => ({
  currentTask: {
    sourceId: '',
    targetId: '',
    tableSelection: { mode: 'all', tables: [] },
    options: {
      mode: 'full',
      structureOptions: { compareIndex: true, compareConstraint: true, compareComment: true },
      dataOptions: { floatPrecision: 6, ignoreCase: false, trimWhitespace: true, dateTimePrecision: 'second', skipLargeFields: false, pageSize: 1000 },
      tableMappings: [],
      ignoreRules: []
    }
  },
  taskStatus: 'idle',
  progress: null,
  taskId: null,

  setSourceDb: (id) => set((state) => ({ currentTask: { ...state.currentTask!, sourceId: id } })),
  setTargetDb: (id) => set((state) => ({ currentTask: { ...state.currentTask!, targetId: id } })),
  setTables: (tables) => set((state) => ({ currentTask: { ...state.currentTask!, tableSelection: tables } })),
  setCompareOptions: (options) => set((state) => ({ currentTask: { ...state.currentTask!, options } })),

  startCompare: async () => {
    const { currentTask } = get();
    if (!currentTask) throw new Error('No task config');
    try {
      set({ taskStatus: 'running' });
      // Mock API call
      // const res = await compareApi.startTask(currentTask);
      const mockTaskId = 'task_' + Date.now();
      set({ taskId: mockTaskId });
      return mockTaskId;
    } catch (e) {
      set({ taskStatus: 'error' });
      throw e;
    }
  },
  resetTask: () => set({ taskStatus: 'idle', progress: null, taskId: null })
}));
