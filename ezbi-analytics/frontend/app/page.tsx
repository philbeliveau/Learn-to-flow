'use client';

import { useState, useEffect } from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import Problems from './components/Problems';
import Services from './components/Services';
import SlackIntegration from './components/SlackIntegration';
import DataProcess from './components/DataProcess';
import TechnicalApproach from './components/TechnicalApproach';
import About from './components/About';
import Pricing from './components/Pricing';
import Contact from './components/Contact';
import Footer from './components/Footer';
import LoginSection from './components/LoginSection';
import Dashboard from './components/Dashboard';

export default function Home() {
  const [currentView, setCurrentView] = useState('home');
  const [apiStatus, setApiStatus] = useState('checking');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);

  // Check API status on mount
  useEffect(() => {
    checkAPIStatus();
  }, []);

  const checkAPIStatus = async () => {
    try {
      const response = await fetch('http://localhost:8004/health');
      if (response.ok) {
        const data = await response.json();
        setApiStatus(data.status === 'healthy' ? 'online' : 'offline');
      } else {
        setApiStatus('offline');
      }
    } catch (error) {
      setApiStatus('offline');
    }
  };

  const handleLogin = (userData: any) => {
    setUser(userData);
    setIsAuthenticated(true);
    setCurrentView('dashboard');
  };

  const handleLogout = () => {
    setUser(null);
    setIsAuthenticated(false);
    setCurrentView('home');
  };

  if (currentView === 'dashboard' && isAuthenticated) {
    return <Dashboard user={user} onLogout={handleLogout} apiStatus={apiStatus} />;
  }

  return (
    <div className="min-h-screen bg-black">
      <Header />
      <main>
        <Hero />
        <Problems />
        <Services />
        <SlackIntegration />
        <DataProcess />
        <TechnicalApproach />
        <About />
        <LoginSection onLogin={handleLogin} apiStatus={apiStatus} />
        <Pricing />
        <Contact />
      </main>
      <Footer />
    </div>
  );
}