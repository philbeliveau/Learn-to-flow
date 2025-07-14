'use client';

import { ReactNode, useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { IntlProvider } from 'react-intl';
import { useUIStore } from '@/store/ui-store';
import { useAuthStore } from '@/store/auth-store';

// Import locale messages
import messagesEn from '@/locales/en.json';
import messagesFr from '@/locales/fr.json';

const messages = {
  en: messagesEn,
  fr: messagesFr,
};

interface ProvidersProps {
  children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  const { language } = useUIStore();
  const { refreshTokenAction } = useAuthStore();
  
  // Create Query Client
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
            retry: (failureCount, error: any) => {
              // Don't retry on authentication errors
              if (error?.status === 401 || error?.status === 403) {
                return false;
              }
              return failureCount < 3;
            },
          },
          mutations: {
            retry: (failureCount, error: any) => {
              // Don't retry on authentication or validation errors
              if (error?.status === 401 || error?.status === 403 || error?.status === 422) {
                return false;
              }
              return failureCount < 2;
            },
          },
        },
      })
  );

  // Auto-refresh token on app start
  useEffect(() => {
    const token = localStorage.getItem('auth-storage');
    if (token) {
      try {
        const authData = JSON.parse(token);
        if (authData.state.refreshToken) {
          refreshTokenAction();
        }
      } catch (error) {
        console.error('Failed to parse auth token:', error);
      }
    }
  }, [refreshTokenAction]);

  // Register service worker
  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/sw.js')
        .then((registration) => {
          console.log('SW registered: ', registration);
        })
        .catch((registrationError) => {
          console.log('SW registration failed: ', registrationError);
        });
    }
  }, []);

  // Handle PWA install prompt
  useEffect(() => {
    let deferredPrompt: any;

    const handler = (e: Event) => {
      e.preventDefault();
      deferredPrompt = e;
    };

    window.addEventListener('beforeinstallprompt', handler);

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <IntlProvider
        locale={language}
        messages={messages[language]}
        defaultLocale="fr"
      >
        {children}
      </IntlProvider>
    </QueryClientProvider>
  );
}