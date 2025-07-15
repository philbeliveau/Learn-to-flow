'use client';

import { useState, useEffect, ReactNode } from 'react';
import { Button } from './button';

interface MobileResponsiveWrapperProps {
  children: ReactNode;
  className?: string;
}

export default function MobileResponsiveWrapper({ children, className = '' }: MobileResponsiveWrapperProps) {
  const [isMobile, setIsMobile] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  if (isMobile) {
    return (
      <div className={`min-h-screen bg-black ${className}`}>
        {/* Mobile Header */}
        <header className="sticky top-0 z-50 bg-black border-b border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xl font-light" style={{color: '#74a6be'}}>E</span>
              <span className="text-xl font-light" style={{color: '#74a6be'}}>Z</span>
              <span className="text-xl font-light" style={{color: '#a7292e'}}>B</span>
              <span className="text-xl font-light" style={{color: '#a7292e'}}>I</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="text-white"
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/>
              </svg>
            </Button>
          </div>
        </header>

        {/* Mobile Navigation Overlay */}
        {sidebarOpen && (
          <div className="fixed inset-0 z-40 bg-black/50" onClick={() => setSidebarOpen(false)}>
            <div className="absolute right-0 top-0 h-full w-80 bg-black border-l border-white/20 p-4">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-light text-white">Navigation</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSidebarOpen(false)}
                  className="text-white"
                >
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                  </svg>
                </Button>
              </div>
              <div className="space-y-4">
                <p className="text-sm text-white/60">
                  This application is optimized for desktop use. For the best experience, please use a desktop or tablet device.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Mobile Content */}
        <div className="p-4">
          <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4 mb-6">
            <h3 className="text-lg font-medium text-yellow-400 mb-2">Mobile Notice</h3>
            <p className="text-sm text-yellow-300/80">
              EZBI Analytics is designed for desktop and tablet use. Some features may be limited on mobile devices.
            </p>
          </div>
          
          <div className="space-y-4">
            <div className="bg-white/5 rounded-lg p-4">
              <h4 className="text-white font-medium mb-2">Recommended Actions:</h4>
              <ul className="text-sm text-white/70 space-y-1">
                <li>• Switch to desktop or tablet for full experience</li>
                <li>• Use landscape orientation if available</li>
                <li>• Enable desktop mode in your browser</li>
              </ul>
            </div>
            
            <div className="bg-white/5 rounded-lg p-4">
              <h4 className="text-white font-medium mb-2">Quick Access:</h4>
              <div className="grid grid-cols-2 gap-2">
                <Button className="w-full text-xs">Dashboard</Button>
                <Button className="w-full text-xs">Financial</Button>
                <Button className="w-full text-xs">Manufacturing</Button>
                <Button className="w-full text-xs">Analytics</Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Desktop/Tablet view
  return (
    <div className={`min-h-screen bg-black ${className}`}>
      {children}
    </div>
  );
}