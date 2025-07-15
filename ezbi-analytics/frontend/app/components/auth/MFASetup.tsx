'use client';

import { useState } from 'react';
import { Button } from '../ui/button';
import { authService, MFASetupData } from '../../services/authService';
import QRCode from 'qrcode';

interface MFASetupProps {
  setupData: MFASetupData;
  onComplete: (user: any) => void;
  onCancel: () => void;
}

export default function MFASetup({ setupData, onComplete, onCancel }: MFASetupProps) {
  const [verificationCode, setVerificationCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [step, setStep] = useState(1);
  const [qrCodeImage, setQrCodeImage] = useState<string>('');

  useState(() => {
    // Generate QR code image
    QRCode.toDataURL(setupData.qr_code)
      .then(url => setQrCodeImage(url))
      .catch(err => console.error('QR code generation failed:', err));
  });

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const success = await authService.verifyMFA(verificationCode);
      
      if (success) {
        const user = authService.getCurrentUser();
        onComplete(user);
      } else {
        setError('Invalid verification code. Please try again.');
      }
    } catch (error) {
      setError('Verification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-black border border-white/20 p-8 rounded-lg">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-light text-white mb-2">
          Multi-Factor Authentication Setup
        </h2>
        <p className="text-sm text-white/60">
          Secure your account with MFA
        </p>
      </div>

      {step === 1 && (
        <div className="space-y-6">
          <div className="text-center">
            <div className="mb-4">
              <h3 className="text-lg font-medium text-white mb-2">Step 1: Scan QR Code</h3>
              <p className="text-sm text-white/70 mb-4">
                Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)
              </p>
            </div>
            
            {qrCodeImage && (
              <div className="bg-white p-4 rounded-lg inline-block mb-4">
                <img src={qrCodeImage} alt="MFA QR Code" className="w-48 h-48" />
              </div>
            )}
            
            <div className="text-center">
              <p className="text-sm text-white/60 mb-2">
                Can't scan? Enter this code manually:
              </p>
              <div className="bg-white/10 p-3 rounded border border-white/20">
                <code className="text-sm text-white font-mono">{setupData.secret}</code>
                <button
                  onClick={() => copyToClipboard(setupData.secret)}
                  className="ml-2 text-xs text-white/60 hover:text-white"
                >
                  Copy
                </button>
              </div>
            </div>
          </div>

          <Button
            onClick={() => setStep(2)}
            className="w-full bg-white/10 hover:bg-white/20 text-white border border-white/30"
          >
            Next: Verify Setup
          </Button>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium text-white mb-2">Step 2: Verify</h3>
            <p className="text-sm text-white/70 mb-4">
              Enter the 6-digit code from your authenticator app
            </p>
          </div>

          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          <form onSubmit={handleVerify} className="space-y-4">
            <div>
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
            </div>

            <div className="flex gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => setStep(1)}
                disabled={loading}
                className="flex-1"
              >
                Back
              </Button>
              <Button
                type="submit"
                disabled={loading || verificationCode.length !== 6}
                className="flex-1 bg-white/10 hover:bg-white/20 text-white border border-white/30"
              >
                {loading ? 'Verifying...' : 'Verify & Complete'}
              </Button>
            </div>
          </form>
        </div>
      )}

      <div className="mt-6 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded">
        <h4 className="text-sm font-medium text-yellow-400 mb-2">Backup Codes</h4>
        <p className="text-xs text-yellow-300/80 mb-3">
          Save these backup codes in a safe place. You can use them to access your account if you lose your device.
        </p>
        <div className="grid grid-cols-2 gap-2 text-xs font-mono">
          {setupData.backup_codes.map((code, index) => (
            <div key={index} className="bg-black/30 p-2 rounded text-center">
              {code}
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6 text-center">
        <Button
          variant="outline"
          onClick={onCancel}
          className="text-white/60 hover:text-white border-white/30"
        >
          Skip for Now
        </Button>
      </div>
    </div>
  );
}