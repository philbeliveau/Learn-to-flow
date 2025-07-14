import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

interface UIState {
  theme: 'light' | 'dark' | 'system';
  language: 'fr' | 'en';
  sidebarCollapsed: boolean;
  notifications: any[];
  modals: Record<string, { isOpen: boolean; data?: any }>;
  toast: {
    isVisible: boolean;
    type: 'success' | 'error' | 'warning' | 'info';
    message: string;
    duration?: number;
  };
}

interface UIStore extends UIState {
  setTheme: (theme: UIState['theme']) => void;
  setLanguage: (language: UIState['language']) => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  addNotification: (notification: any) => void;
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
            state.notifications = state.notifications.filter((n: any) => n.id !== id);
          });
        },

        markNotificationAsRead: (id) => {
          set((state) => {
            const notification = state.notifications.find((n: any) => n.id === id);
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