import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { useAuthStore } from './auth-store';

interface ManufacturingData {
  id: string;
  timestamp: Date;
  production: {
    quantity: number;
    target: number;
    efficiency: number;
  };
  quality: {
    defectRate: number;
    qualityScore: number;
  };
  machine: {
    id: string;
    name: string;
    status: 'running' | 'stopped' | 'maintenance';
    temperature: number;
    pressure: number;
    vibration: number;
  };
  material: {
    batchId: string;
    supplier: string;
    grade: string;
  };
}

interface DataState {
  manufacturingData: ManufacturingData[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  totalRecords: number;
  pageSize: number;
  currentPage: number;
  searchQuery: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

interface DataStore extends DataState {
  fetchData: (params?: any) => Promise<void>;
  addData: (data: ManufacturingData[]) => void;
  updateData: (id: string, updates: Partial<ManufacturingData>) => void;
  deleteData: (id: string) => void;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  setSearchQuery: (query: string) => void;
  setSorting: (field: string, order: 'asc' | 'desc') => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useDataStore = create<DataStore>()(
  devtools(
    immer((set, get) => ({
      manufacturingData: [],
      isLoading: false,
      error: null,
      lastUpdated: null,
      totalRecords: 0,
      pageSize: 50,
      currentPage: 1,
      searchQuery: '',
      sortBy: 'timestamp',
      sortOrder: 'desc',

      fetchData: async (params = {}) => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const { token } = useAuthStore.getState();
          const { currentPage, pageSize, searchQuery, sortBy, sortOrder } = get();
          
          const queryParams = new URLSearchParams({
            page: currentPage.toString(),
            pageSize: pageSize.toString(),
            search: searchQuery,
            sortBy,
            sortOrder,
            ...params,
          });

          const response = await fetch(`/api/data?${queryParams}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            throw new Error('Failed to fetch data');
          }

          const data = await response.json();
          
          set((state) => {
            state.manufacturingData = data.data;
            state.totalRecords = data.pagination.total;
            state.isLoading = false;
            state.lastUpdated = new Date();
          });
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Unknown error';
            state.isLoading = false;
          });
        }
      },

      addData: (data) => {
        set((state) => {
          state.manufacturingData = [...data, ...state.manufacturingData];
          state.totalRecords += data.length;
        });
      },

      updateData: (id, updates) => {
        set((state) => {
          const index = state.manufacturingData.findIndex((d: ManufacturingData) => d.id === id);
          if (index !== -1) {
            state.manufacturingData[index] = { ...state.manufacturingData[index], ...updates };
          }
        });
      },

      deleteData: (id) => {
        set((state) => {
          state.manufacturingData = state.manufacturingData.filter((d: ManufacturingData) => d.id !== id);
          state.totalRecords -= 1;
        });
      },

      setPage: (page) => {
        set((state) => {
          state.currentPage = page;
        });
      },

      setPageSize: (pageSize) => {
        set((state) => {
          state.pageSize = pageSize;
          state.currentPage = 1;
        });
      },

      setSearchQuery: (query) => {
        set((state) => {
          state.searchQuery = query;
          state.currentPage = 1;
        });
      },

      setSorting: (field, order) => {
        set((state) => {
          state.sortBy = field;
          state.sortOrder = order;
          state.currentPage = 1;
        });
      },

      setLoading: (loading) => {
        set((state) => {
          state.isLoading = loading;
        });
      },

      setError: (error) => {
        set((state) => {
          state.error = error;
        });
      },
    })),
    { name: 'data-store' }
  )
);