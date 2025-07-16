'use client';

import { useState } from 'react';
import { Button } from '../ui/button';
import { authService, LoginCredentials, AuthResponse } from '../../services/authService';
import MFASetup from './MFASetup';
import MFAVerification from './MFAVerification';
import { EnvValidationResult } from '../../utils/envValidation';
import { ConnectionStatus } from '../../utils/connectionMonitor';

interface LoginFormProps {
  onLogin: (user: any) => void;
  apiStatus: string;
  envValidation?: EnvValidationResult | null;
  connectionStatus?: ConnectionStatus | null;
}

export default function LoginForm({ onLogin, apiStatus, envValidation, connectionStatus }: LoginFormProps) {
  const [formData, setFormData] = useState<LoginCredentials>({
    email: '',
    password: '',
    mfa_code: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [requiresMFA, setRequiresMFA] = useState(false);
  const [showMFASetup, setShowMFASetup] = useState(false);
  const [authResponse, setAuthResponse] = useState<AuthResponse | null>(null);
  const [showDebugInfo, setShowDebugInfo] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    console.log('🔐 Form submitted with:', { email: formData.email, password: '***' });

    try {
      const response = await authService.login(formData);
      setAuthResponse(response);

      if (response.success && response.user) {
        onLogin(response.user);
      } else if (response.requires_mfa) {
        setRequiresMFA(true);
      } else if (response.mfa_setup) {
        setShowMFASetup(true);
      } else {
        setError(response.message || 'Login failed');
      }
    } catch (error) {
      console.error('🚨 Login error details:', error);
      console.error('🚨 Error type:', typeof error);
      console.error('🚨 Error name:', error instanceof Error ? error.name : 'Unknown');
      console.error('🚨 Error message:', error instanceof Error ? error.message : 'No message');
      console.error('🚨 Error stack:', error instanceof Error ? error.stack : 'No stack');
      
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      
      // Provide more user-friendly error messages
      if (errorMessage.includes('fetch') || errorMessage.includes('Failed to fetch')) {
        setError('Unable to connect to server. Please check your connection and try again.');
      } else if (errorMessage.includes('401')) {
        setError('Invalid email or password. Please check your credentials.');
      } else if (errorMessage.includes('timeout')) {
        setError('Connection timeout. Please try again.');
      } else {
        setError(`Connection error: ${errorMessage}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleMFAComplete = (user: any) => {
    setRequiresMFA(false);
    setShowMFASetup(false);
    onLogin(user);
  };

  const testConnection = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      console.log('🔍 Testing connection to:', apiUrl);
      
      const response = await fetch(`${apiUrl}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      console.log('📡 Response status:', response.status);
      console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()));
      
      const data = await response.json();
      console.log('📊 Response data:', data);
      
      alert(`✅ Connection test SUCCESS!\n\nStatus: ${response.status}\nData: ${JSON.stringify(data, null, 2)}`);
    } catch (error) {
      console.error('❌ Connection test failed:', error);
      alert(`❌ Connection test FAILED!\n\nError: ${error}\n\nCheck browser console for details.`);
    }
  };

  if (showMFASetup && authResponse?.mfa_setup) {
    return (
      <MFASetup 
        setupData={authResponse.mfa_setup}
        onComplete={handleMFAComplete}
        onCancel={() => setShowMFASetup(false)}
      />
    );
  }

  if (requiresMFA) {
    return (
      <MFAVerification
        email={formData.email}
        onComplete={handleMFAComplete}
        onCancel={() => setRequiresMFA(false)}
      />
    );
  }

  return (
    <section id="login-section" className="py-20 bg-black">
      <div className="container mx-auto px-4">
        <div className="max-w-md mx-auto bg-black border border-white/20 p-8 rounded-lg">
          {/* EZBI Logo */}
          <div className="text-center mb-8">
            <div className="flex justify-center items-center gap-1 mb-4">
              <span className="text-4xl font-light" style={{color: '#74a6be'}}>E</span>
              <span className="text-4xl font-light" style={{color: '#74a6be'}}>Z</span>
              <span className="text-4xl font-light" style={{color: '#a7292e'}}>B</span>
              <span className="text-4xl font-light" style={{color: '#a7292e'}}>I</span>
            </div>
            <h2 className="text-2xl font-light text-white mb-2">
              Secure Access
            </h2>
            <p className="text-sm text-white/60">
              Enhanced security with JWT & MFA
            </p>
          </div>

          {/* API Status */}
          <div className="flex items-center justify-center gap-2 mb-6">
            <div className={`w-2 h-2 rounded-full ${
              apiStatus === 'online' ? 'bg-green-500' : 
              apiStatus === 'offline' ? 'bg-red-500' : 
              'bg-yellow-500 animate-pulse'
            }`}></div>
            <span className="text-sm font-light text-white/70">
              {apiStatus === 'online' ? 'System Online' : 
               apiStatus === 'offline' ? 'System Offline' : 
               'Checking Status...'}
            </span>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium mb-2 text-white/80">
                Email Address
              </label>
              <input
                type="email"
                required
                className="w-full px-4 py-3 bg-black border border-white/30 rounded focus:border-white/60 focus:outline-none text-white placeholder-white/40"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="Enter your email"
                disabled={loading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2 text-white/80">
                Password
              </label>
              <input
                type="password"
                required
                className="w-full px-4 py-3 bg-black border border-white/30 rounded focus:border-white/60 focus:outline-none text-white placeholder-white/40"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                placeholder="Enter your password"
                disabled={loading}
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-white/10 hover:bg-white/20 text-white border border-white/30 hover:border-white/60 disabled:opacity-50"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  Signing In...
                </div>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>

          {/* Demo Credentials */}
          <div className="mt-8 p-4 bg-white/5 border border-white/10 rounded">
            <p className="text-sm text-white/60 mb-2">Demo Credentials:</p>
            <div className="space-y-1 text-sm">
              <p className="text-white/80">
                <span className="text-white">Admin:</span> admin@ezbi.com / admin
              </p>
              <p className="text-white/80">
                <span className="text-white">User:</span> user@ezbi.com / password
              </p>
              <p className="text-white/80">
                <span className="text-white">Demo:</span> demo@ezbi.com / demo
              </p>
            </div>
          </div>

          {/* Security Features */}
          <div className="mt-6 text-center">
            <div className="flex justify-center items-center gap-4 text-xs text-white/50">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span>JWT Security</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span>MFA Support</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span>Role-Based Access</span>
              </div>
            </div>
          </div>

          {/* API Documentation Link */}
          <div className="text-center mt-6">
            <a 
              href="http://localhost:8000/docs" 
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-white/60 hover:text-white/80 transition-colors"
            >
              API Documentation
            </a>
          </div>

          {/* Debug Information */}
          <div className="text-center mt-4">
            <button
              onClick={() => setShowDebugInfo(!showDebugInfo)}
              className="text-xs text-white/40 hover:text-white/60 transition-colors"
            >
              {showDebugInfo ? 'Hide' : 'Show'} Debug Info
            </button>
            {showDebugInfo && (
              <div className="mt-2 p-3 bg-black/50 border border-white/10 rounded text-xs text-white/70">
                <div className="space-y-1">
                  <div>API URL: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</div>
                  <div>API Status: {apiStatus}</div>
                  {envValidation && (
                    <div className={`text-xs ${envValidation.isValid ? 'text-green-400' : 'text-red-400'}`}>
                      Environment: {envValidation.isValid ? '✅ Valid' : '❌ Issues detected'}
                    </div>
                  )}
                  {connectionStatus && (
                    <div className="text-xs space-y-1">
                      <div className={connectionStatus.isConnected ? 'text-green-400' : 'text-red-400'}>
                        Connection: {connectionStatus.isConnected ? '✅ Connected' : '❌ Disconnected'}
                      </div>
                      {connectionStatus.responseTime && (
                        <div className="text-blue-400">Response: {connectionStatus.responseTime}ms</div>
                      )}
                      {connectionStatus.consecutiveFailures > 0 && (
                        <div className="text-yellow-400">Failures: {connectionStatus.consecutiveFailures}</div>
                      )}
                      <div className="text-gray-400">Uptime: {connectionStatus.uptime.toFixed(1)}%</div>
                    </div>
                  )}
                  <div className="flex gap-2">
                    <button
                      onClick={testConnection}
                      className="px-2 py-1 bg-white/10 hover:bg-white/20 rounded text-xs"
                    >
                      Test Connection
                    </button>
                    <button
                      onClick={async () => {
                        try {
                          const testLogin = await authService.login({ email: 'demo@ezbi.com', password: 'demo' });
                          alert(`Direct login test: ${JSON.stringify(testLogin, null, 2)}`);
                        } catch (error) {
                          alert(`Direct login failed: ${error}`);
                        }
                      }}
                      className="px-2 py-1 bg-blue-500/20 hover:bg-blue-500/40 rounded text-xs"
                    >
                      Test Login
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}