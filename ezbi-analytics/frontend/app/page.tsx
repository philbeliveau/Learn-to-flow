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
      // Check auth API on port 8004 (primary for authentication)
      const response = await fetch('http://localhost:8004/health');
      if (response.ok) {
        const data = await response.json();
        setApiStatus(data.status === 'healthy' ? 'online' : 'offline');
      } else {
        setApiStatus('offline');
      }
    } catch (error) {
      console.warn('Auth API (8004) unavailable, checking manufacturing API (8003)');
      try {
        // Fallback to port 8003 for manufacturing data
        const fallbackResponse = await fetch('http://localhost:8003/health');
        if (fallbackResponse.ok) {
          const data = await fallbackResponse.json();
          setApiStatus(data.status === 'healthy' ? 'online' : 'offline');
        } else {
          setApiStatus('offline');
        }
      } catch (fallbackError) {
        setApiStatus('offline');
      }
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