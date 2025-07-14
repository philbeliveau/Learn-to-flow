import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Providers } from './providers';
import { ThemeProvider } from '@/components/theme-provider';
import { Toaster } from 'react-hot-toast';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'EZBI Analytics - Prédiction de Trésorerie IA',
  description: 'Solution IA de prédiction de trésorerie pour les PME manufacturières françaises',
  keywords: ['trésorerie', 'cash flow', 'prédiction', 'manufacturing', 'AI', 'analytics', 'industrie 4.0', 'PME', 'finance'],
  authors: [{ name: 'EZBI Analytics Team' }],
  creator: 'EZBI Analytics',
  publisher: 'EZBI Analytics',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL('https://ezbi-analytics.com'),
  alternates: {
    canonical: '/',
    languages: {
      'fr-CA': '/fr',
      'en-CA': '/en',
    },
  },
  openGraph: {
    title: 'EZBI Analytics - Prédiction de Trésorerie IA',
    description: 'Solution IA de prédiction de trésorerie pour les PME manufacturières françaises',
    url: 'https://ezbi-analytics.com',
    siteName: 'EZBI Analytics',
    images: [
      {
        url: '/images/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'EZBI Analytics - Manufacturing Intelligence Platform',
      },
    ],
    locale: 'fr_CA',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'EZBI Analytics - Prédiction de Trésorerie IA',
    description: 'Solution IA de prédiction de trésorerie pour les PME manufacturières françaises',
    images: ['/images/twitter-image.jpg'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'EZBI Analytics',
    startupImage: [
      '/images/apple-touch-startup-image-768x1004.png',
      '/images/apple-touch-startup-image-1536x2008.png',
    ],
  },
  other: {
    'mobile-web-app-capable': 'yes',
    'apple-mobile-web-app-status-bar-style': 'black-translucent',
    'theme-color': '#2563eb',
    'color-scheme': 'light dark',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className={inter.variable}>
      <body className={`${inter.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}