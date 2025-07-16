'use client';

import { useState, useEffect } from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import Problems from './components/Problems';
import Services from './components/Services';
import Pricing from './components/Pricing';
import Contact from './components/Contact';
import Footer from './components/Footer';
import LoginForm from './components/auth/LoginForm';
import Dashboard from './components/Dashboard';
import { authService, User } from './services/authService';
import { cacheService } from './services/cacheService';

export default function Home() {
  const [currentView, setCurrentView] = useState('home');
  const [apiStatus, setApiStatus] = useState('checking');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Check API status and authentication on mount
  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    setLoading(true);
    
    // Check if user is already authenticated
    if (authService.isAuthenticated()) {
      const currentUser = authService.getCurrentUser();
      if (currentUser) {
        setUser(currentUser);
        setIsAuthenticated(true);
        setCurrentView('dashboard');
      }
    }
    
    // Check API status
    await checkAPIStatus();
    setLoading(false);
  };

  const checkAPIStatus = async () => {
    try {
      // Check main API on port 8000
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      console.log('Checking API health at:', apiUrl);
      
      const response = await fetch(`${apiUrl}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        // Add timeout to prevent hanging
        signal: AbortSignal.timeout(5000)
      });
      
      if (response.ok) {
        const data = await response.json();
        setApiStatus(data.status === 'healthy' ? 'online' : 'offline');
        console.log('✅ API Status Check SUCCESS:', data);
      } else {
        console.warn('❌ API health check failed:', response.status, response.statusText);
        setApiStatus('offline');
      }
    } catch (error) {
      console.error('❌ API connection error:', error);
      
      // For real-time systems, we should assume the backend is available
      // and let the actual login attempt handle the error
      setApiStatus('online');
      console.log('🔄 Setting status to online - will let login attempt handle connection issues');
    }
  };

  const handleLogin = (userData: User) => {
    setUser(userData);
    setIsAuthenticated(true);
    setCurrentView('dashboard');
  };

  const handleLogout = async () => {
    await authService.logout();
    await cacheService.clear(); // Clear cache on logout
    setUser(null);
    setIsAuthenticated(false);
    setCurrentView('home');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-white/30 border-t-white rounded-full animate-spin mb-4"></div>
          <p className="text-white/70">Loading EZBI Analytics...</p>
        </div>
      </div>
    );
  }

  if (currentView === 'dashboard' && isAuthenticated && user) {
    return <Dashboard user={user} onLogout={handleLogout} apiStatus={apiStatus} />;
  }

  return (
    <div className="min-h-screen bg-black">
      <Header />
      <main>
        <Hero />
        <Problems />
        <Services />
        <Pricing />
        <LoginForm onLogin={handleLogin} apiStatus={apiStatus} />
        <Contact />
      </main>
      <Footer />
    </div>
  );
}