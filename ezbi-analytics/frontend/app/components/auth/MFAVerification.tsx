'use client';

import { useState } from 'react';
import { Button } from '../ui/button';
import { authService } from '../../services/authService';

interface MFAVerificationProps {
  email: string;
  onComplete: (user: any) => void;
  onCancel: () => void;
}

export default function MFAVerification({ email, onComplete, onCancel }: MFAVerificationProps) {
  const [verificationCode, setVerificationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await authService.login({
        email,
        password: '', // Password already validated in previous step
        mfa_code: verificationCode
      });

      if (response.success && response.user) {
        onComplete(response.user);
      } else {
        setError(response.message || 'Invalid verification code');
      }
    } catch (error) {
      setError('Verification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-black border border-white/20 p-8 rounded-lg">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-light text-white mb-2">
          Two-Factor Authentication
        </h2>
        <p className="text-sm text-white/60">
          Enter the code from your authenticator app
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      <form onSubmit={handleVerify} className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2 text-white/80">
            Verification Code
          </label>
          <input
            type="text"
            required
            maxLength={6}
            className="w-full px-4 py-3 bg-black border border-white/30 rounded focus:border-white/60 focus:outline-none text-white text-center text-2xl font-mono tracking-widest"
            value={verificationCode}
            onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
            placeholder="000000"
            disabled={loading}
          />
          <p className="text-xs text-white/50 mt-1">
            Enter the 6-digit code from your authenticator app
          </p>
        </div>

        <div className="flex gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={loading}
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={loading || verificationCode.length !== 6}
            className="flex-1 bg-white/10 hover:bg-white/20 text-white border border-white/30"
          >
            {loading ? 'Verifying...' : 'Verify'}
          </Button>
        </div>
      </form>

      <div className="mt-6 text-center">
        <p className="text-xs text-white/50">
          Having trouble? Contact support for assistance
        </p>
      </div>
    </div>
  );
}