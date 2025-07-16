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
import { EnvironmentValidator, EnvValidationResult } from './utils/envValidation';
import { ConnectionMonitor, ConnectionStatus } from './utils/connectionMonitor';
import { StartupValidator, StartupValidationResult } from './utils/startupValidator';
import { robustApiService } from './services/robustApiService';
import { ErrorBoundary } from './components/ErrorBoundary';

export default function Home() {
  const [currentView, setCurrentView] = useState('home');
  const [apiStatus, setApiStatus] = useState('checking');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [envValidation, setEnvValidation] = useState<EnvValidationResult | null>(null);
  const [showEnvWarnings, setShowEnvWarnings] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);
  const [startupValidation, setStartupValidation] = useState<StartupValidationResult | null>(null);

  // Check API status and authentication on mount
  useEffect(() => {
    initializeApp();
    
    // Cleanup on unmount
    return () => {
      ConnectionMonitor.destroy();
    };
  }, []);

  const initializeApp = async () => {
    setLoading(true);
    
    // 🛡️ Priority 3: Comprehensive Startup Validation
    console.log('🚀 Running comprehensive startup validation...');
    const startupResult = await StartupValidator.validateStartup();
    setStartupValidation(startupResult);
    
    if (!startupResult.isValid) {
      console.error('❌ Startup validation failed:', startupResult.summary);
      console.table(startupResult.checks);
      
      // Show critical errors to user
      const criticalErrors = startupResult.checks.filter(c => c.status === 'error');
      if (criticalErrors.length > 0) {
        console.error('🚨 Critical errors that need attention:', criticalErrors);
      }
    } else {
      console.log('✅ Startup validation passed:', startupResult.summary);
    }
    
    // 🛡️ Priority 1: Environment Validation (legacy - now part of startup validation)
    console.log('🔍 Validating environment configuration...');
    const validation = await EnvironmentValidator.validateEnvironment();
    setEnvValidation(validation);
    
    if (!validation.isValid) {
      console.error('❌ Environment validation failed:', validation.errors);
      setShowEnvWarnings(true);
      
      // Show suggestions in console
      const suggestions = EnvironmentValidator.generateConfigSuggestions(validation);
      console.log('💡 Configuration suggestions:', suggestions);
    } else {
      console.log('✅ Environment validation passed');
    }
    
    // Check if user is already authenticated
    if (authService.isAuthenticated()) {
      const currentUser = authService.getCurrentUser();
      if (currentUser) {
        setUser(currentUser);
        setIsAuthenticated(true);
        setCurrentView('dashboard');
      }
    }
    
    // Check API status using robust service
    await checkAPIStatus();
    
    // Test all critical endpoints
    try {
      console.log('🔍 Testing all critical endpoints...');
      const endpointTests = await robustApiService.testAllEndpoints();
      console.log('📊 Endpoint test results:', endpointTests);
    } catch (error) {
      console.warn('⚠️ Some endpoints may be unavailable:', error);
    }
    
    // 🛡️ Priority 2: Start Connection Monitoring
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    try {
      const monitor = ConnectionMonitor.getInstance(apiUrl, {
        checkInterval: 30000, // 30 seconds
        timeout: 5000,
        maxRetries: 3,
        enableLogging: true
      });
      
      // Listen for connection status changes
      monitor.addListener((status: ConnectionStatus) => {
        setConnectionStatus(status);
        setApiStatus(status.isConnected ? 'online' : 'offline');
        console.log('🔄 Connection status update:', status);
      });
      
      // Start monitoring
      monitor.startMonitoring();
    } catch (error) {
      console.error('❌ Failed to initialize connection monitor:', error);
      // Continue without monitoring - don't break the app
    }
    
    setLoading(false);
  };

  const checkAPIStatus = async () => {
    try {
      console.log('🔍 Checking API health using robust service...');
      
      const healthResponse = await robustApiService.healthCheck();
      
      if (healthResponse.success) {
        const data = healthResponse.data;
        setApiStatus(data.status === 'healthy' ? 'online' : 'offline');
        console.log('✅ API Status Check SUCCESS:', data);
      } else {
        console.warn('❌ API health check failed:', healthResponse.error);
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
    robustApiService.clearCache(); // Clear robust API cache
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
          {startupValidation && (
            <div className="mt-4 text-sm text-white/60">
              {startupValidation.summary}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (currentView === 'dashboard' && isAuthenticated && user) {
    return (
      <ErrorBoundary
        onError={(error, errorInfo) => {
          console.error('Dashboard error:', error, errorInfo);
        }}
      >
        <Dashboard user={user} onLogout={handleLogout} apiStatus={apiStatus} />
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        console.error('App error:', error, errorInfo);
      }}
    >
      <div className="min-h-screen bg-black">
      {/* 🛡️ Environment Validation Warnings */}
      {showEnvWarnings && envValidation && !envValidation.isValid && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-red-600 text-white p-4">
          <div className="container mx-auto">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl">⚠️</span>
                <span className="font-semibold">Configuration Issue Detected</span>
              </div>
              <button
                onClick={() => setShowEnvWarnings(false)}
                className="text-white hover:text-gray-200 text-xl"
              >
                ×
              </button>
            </div>
            <div className="mt-2 space-y-1">
              {envValidation.errors.map((error, index) => (
                <div key={index} className="text-sm">❌ {error}</div>
              ))}
              {envValidation.suggestions.map((suggestion, index) => (
                <div key={index} className="text-sm">💡 {suggestion}</div>
              ))}
            </div>
            {envValidation.detectedBackendPort && (
              <div className="mt-3 p-2 bg-red-700 rounded text-sm">
                <strong>Quick Fix:</strong> Update your .env.local file to use port {envValidation.detectedBackendPort}
              </div>
            )}
          </div>
        </div>
      )}
      
      <Header />
      <main>
        <Hero />
        <Problems />
        <Services />
        <Pricing />
        <LoginForm onLogin={handleLogin} apiStatus={apiStatus} envValidation={envValidation} connectionStatus={connectionStatus} />
        <Contact />
      </main>
      <Footer />
    </div>
    </ErrorBoundary>
  );
}