import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type { 
  AppState, 
  AuthState, 
  DashboardState, 
  PredictionState, 
  DataState, 
  UIState,
  User,
  PredictionResult,
  MLModel,
  ManufacturingData,
  Notification
} from '@/types';

// Auth Store
interface AuthStore extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  updateUser: (user: Partial<User>) => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthStore>()(
  devtools(
    persist(
      immer((set, get) => ({
        user: null,
        token: null,
        refreshToken: null,
        isLoading: false,
        isAuthenticated: false,

        login: async (email: string, password: string) => {
          set((state) => {
            state.isLoading = true;
          });

          try {
            const response = await fetch('/api/auth/login', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ email, password }),
            });

            if (!response.ok) {
              throw new Error('Login failed');
            }

            const data = await response.json();
            
            set((state) => {
              state.user = data.user;
              state.token = data.token;
              state.refreshToken = data.refreshToken;
              state.isAuthenticated = true;
              state.isLoading = false;
            });
          } catch (error) {
            set((state) => {
              state.isLoading = false;
              state.isAuthenticated = false;
            });
            throw error;
          }
        },

        logout: () => {
          set((state) => {
            state.user = null;
            state.token = null;
            state.refreshToken = null;
            state.isAuthenticated = false;
          });
        },

        refreshToken: async () => {
          const { refreshToken } = get();
          if (!refreshToken) return;

          try {
            const response = await fetch('/api/auth/refresh', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ refreshToken }),
            });

            if (!response.ok) {
              throw new Error('Token refresh failed');
            }

            const data = await response.json();
            
            set((state) => {
              state.token = data.token;
              state.refreshToken = data.refreshToken;
            });
          } catch (error) {
            set((state) => {
              state.user = null;
              state.token = null;
              state.refreshToken = null;
              state.isAuthenticated = false;
            });
          }
        },

        updateUser: (userData: Partial<User>) => {
          set((state) => {
            if (state.user) {
              state.user = { ...state.user, ...userData };
            }
          });
        },

        setLoading: (loading: boolean) => {
          set((state) => {
            state.isLoading = loading;
          });
        },
      })),
      {
        name: 'auth-storage',
        partialize: (state) => ({
          user: state.user,
          token: state.token,
          refreshToken: state.refreshToken,
          isAuthenticated: state.isAuthenticated,
        }),
      }
    ),
    { name: 'auth-store' }
  )
);

// Dashboard Store
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

// Prediction Store
interface PredictionStore extends PredictionState {
  fetchPredictions: () => Promise<void>;
  addPrediction: (prediction: PredictionResult) => void;
  updatePrediction: (id: string, updates: Partial<PredictionResult>) => void;
  deletePrediction: (id: string) => void;
  fetchModels: () => Promise<void>;
  selectModel: (model: MLModel) => void;
  updateFilters: (filters: Partial<PredictionState['filters']>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const usePredictionStore = create<PredictionStore>()(
  devtools(
    immer((set, get) => ({
      predictions: [],
      isLoading: false,
      error: null,
      models: [],
      selectedModel: null,
      filters: {},

      fetchPredictions: async () => {
        set((state) => {
          state.isLoading = true;
          state.error = null;
        });

        try {
          const { token } = useAuthStore.getState();
          const response = await fetch('/api/predictions', {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            throw new Error('Failed to fetch predictions');
          }

          const data = await response.json();
          
          set((state) => {
            state.predictions = data.data;
            state.isLoading = false;
          });
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Unknown error';
            state.isLoading = false;
          });
        }
      },

      addPrediction: (prediction) => {
        set((state) => {
          state.predictions.unshift(prediction);
        });
      },

      updatePrediction: (id, updates) => {
        set((state) => {
          const index = state.predictions.findIndex(p => p.id === id);
          if (index !== -1) {
            state.predictions[index] = { ...state.predictions[index], ...updates };
          }
        });
      },

      deletePrediction: (id) => {
        set((state) => {
          state.predictions = state.predictions.filter(p => p.id !== id);
        });
      },

      fetchModels: async () => {
        try {
          const { token } = useAuthStore.getState();
          const response = await fetch('/api/models', {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            throw new Error('Failed to fetch models');
          }

          const data = await response.json();
          
          set((state) => {
            state.models = data.data;
          });
        } catch (error) {
          set((state) => {
            state.error = error instanceof Error ? error.message : 'Unknown error';
          });
        }
      },

      selectModel: (model) => {
        set((state) => {
          state.selectedModel = model;
        });
      },

      updateFilters: (filters) => {
        set((state) => {
          state.filters = { ...state.filters, ...filters };
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
    { name: 'prediction-store' }
  )
);

// Data Store
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
          const index = state.manufacturingData.findIndex(d => d.id === id);
          if (index !== -1) {
            state.manufacturingData[index] = { ...state.manufacturingData[index], ...updates };
          }
        });
      },

      deleteData: (id) => {
        set((state) => {
          state.manufacturingData = state.manufacturingData.filter(d => d.id !== id);
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

// UI Store
interface UIStore extends UIState {
  setTheme: (theme: UIState['theme']) => void;
  setLanguage: (language: UIState['language']) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  markNotificationAsRead: (id: string) => void;
  clearNotifications: () => void;
  openModal: (modalKey: string, data?: any) => void;
  closeModal: (modalKey: string) => void;
  showToast: (type: UIState['toast']['type'], message: string, duration?: number) => void;
  hideToast: () => void;
}

export const useUIStore = create<UIStore>()(
  devtools(
    persist(
      immer((set, get) => ({
        theme: 'system',
        language: 'fr',
        sidebarCollapsed: false,
        notifications: [],
        modals: {},
        toast: {
          isVisible: false,
          type: 'info',
          message: '',
        },

        setTheme: (theme) => {
          set((state) => {
            state.theme = theme;
          });
        },

        setLanguage: (language) => {
          set((state) => {
            state.language = language;
          });
        },

        toggleSidebar: () => {
          set((state) => {
            state.sidebarCollapsed = !state.sidebarCollapsed;
          });
        },

        setSidebarCollapsed: (collapsed) => {
          set((state) => {
            state.sidebarCollapsed = collapsed;
          });
        },

        addNotification: (notification) => {
          set((state) => {
            state.notifications.unshift({
              ...notification,
              id: Date.now().toString(),
              read: false,
            });
          });
        },

        removeNotification: (id) => {
          set((state) => {
            state.notifications = state.notifications.filter(n => n.id !== id);
          });
        },

        markNotificationAsRead: (id) => {
          set((state) => {
            const notification = state.notifications.find(n => n.id === id);
            if (notification) {
              notification.read = true;
            }
          });
        },

        clearNotifications: () => {
          set((state) => {
            state.notifications = [];
          });
        },

        openModal: (modalKey, data) => {
          set((state) => {
            state.modals[modalKey] = { isOpen: true, data };
          });
        },

        closeModal: (modalKey) => {
          set((state) => {
            state.modals[modalKey] = { isOpen: false };
          });
        },

        showToast: (type, message, duration = 5000) => {
          set((state) => {
            state.toast = { isVisible: true, type, message, duration };
          });
        },

        hideToast: () => {
          set((state) => {
            state.toast.isVisible = false;
          });
        },
      })),
      {
        name: 'ui-storage',
        partialize: (state) => ({
          theme: state.theme,
          language: state.language,
          sidebarCollapsed: state.sidebarCollapsed,
        }),
      }
    ),
    { name: 'ui-store' }
  )
);