'use client';

import { useState } from 'react';
import { Button } from '../ui/button';
import { authService, LoginCredentials, AuthResponse } from '../../services/authService';
import MFASetup from './MFASetup';
import MFAVerification from './MFAVerification';

interface LoginFormProps {
  onLogin: (user: any) => void;
  apiStatus: string;
}

export default function LoginForm({ onLogin, apiStatus }: LoginFormProps) {
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

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
      setError(error instanceof Error ? error.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleMFAComplete = (user: any) => {
    setRequiresMFA(false);
    setShowMFASetup(false);
    onLogin(user);
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
              disabled={loading || apiStatus === 'offline'}
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
              href="http://localhost:8004/docs" 
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-white/60 hover:text-white/80 transition-colors"
            >
              API Documentation
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}