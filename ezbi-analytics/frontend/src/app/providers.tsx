'use client';

import { ReactNode, useEffect } from 'react';
import { IntlProvider } from 'react-intl';
import { useUIStore } from '@/store';
import { useAuthStore } from '@/store';

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
  const { refreshToken } = useAuthStore();

  // Auto-refresh token on app start
  useEffect(() => {
    const token = localStorage.getItem('auth-storage');
    if (token) {
      try {
        const authData = JSON.parse(token);
        if (authData.state.refreshToken) {
          refreshToken();
        }
      } catch (error) {
        console.error('Failed to parse auth token:', error);
      }
    }
  }, [refreshToken]);

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
    <IntlProvider
      locale={language}
      messages={messages[language]}
      defaultLocale="fr"
    >
      {children}
    </IntlProvider>
  );
}