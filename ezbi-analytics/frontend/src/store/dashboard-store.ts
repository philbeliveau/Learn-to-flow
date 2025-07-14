import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

interface DashboardState {
  currentView: 'overview' | 'analytics' | 'models' | 'alerts';
  selectedTimeRange: '24h' | '7d' | '30d' | '90d' | 'custom';
  customTimeRange?: { start: Date; end: Date };
  filters: Record<string, any>;
  refreshInterval: number;
  isRealTime: boolean;
}

interface DashboardStore extends DashboardState {
  setCurrentView: (view: DashboardState['currentView']) => void;
  setTimeRange: (range: DashboardState['selectedTimeRange']) => void;
  setCustomTimeRange: (start: Date, end: Date) => void;
  updateFilters: (filters: Partial<DashboardState['filters']>) => void;
  setRefreshInterval: (interval: number) => void;
  toggleRealTime: () => void;
}

export const useDashboardStore = create<DashboardStore>()(
  devtools(
    immer((set) => ({
      currentView: 'overview',
      selectedTimeRange: '24h',
      customTimeRange: undefined,
      filters: {},
      refreshInterval: 30000, // 30 seconds
      isRealTime: false,

      setCurrentView: (view) => {
        set((state) => {
          state.currentView = view;
        });
      },

      setTimeRange: (range) => {
        set((state) => {
          state.selectedTimeRange = range;
          if (range !== 'custom') {
            state.customTimeRange = undefined;
          }
        });
      },

      setCustomTimeRange: (start, end) => {
        set((state) => {
          state.selectedTimeRange = 'custom';
          state.customTimeRange = { start, end };
        });
      },

      updateFilters: (filters) => {
        set((state) => {
          state.filters = { ...state.filters, ...filters };
        });
      },

      setRefreshInterval: (interval) => {
        set((state) => {
          state.refreshInterval = interval;
        });
      },

      toggleRealTime: () => {
        set((state) => {
          state.isRealTime = !state.isRealTime;
        });
      },
    })),
    { name: 'dashboard-store' }
  )
);