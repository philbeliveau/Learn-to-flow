'use client';

import React from 'react';

interface NavigationTab {
  id: string;
  name: string;
  icon: JSX.Element;
  color: string;
}

interface NavigationSidebarProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

const NavigationSidebar: React.FC<NavigationSidebarProps> = ({ activeTab, onTabChange }) => {
  const tabs: NavigationTab[] = [
    {
      id: 'overview',
      name: 'Vue d\'ensemble',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>
        </svg>
      ),
      color: '#74a6be'
    },
    {
      id: 'financial',
      name: 'Financier',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M7 15h2c0 1.08 1.37 2 3 2s3-.92 3-2c0-1.1-1.04-1.5-3.24-2.03C9.64 12.44 7 11.78 7 9c0-1.79 1.47-3.31 3.5-3.82V3h3v2.18C15.53 5.69 17 7.21 17 9h-2c0-1.08-1.37-2-3-2s-3 .92-3 2c0 1.1 1.04 1.5 3.24 2.03C14.36 11.56 17 12.22 17 15c0 1.79-1.47 3.31-3.5 3.82V21h-3v-2.18C8.47 18.31 7 16.79 7 15z"/>
        </svg>
      ),
      color: '#a7292e'
    },
    {
      id: 'manufacturing',
      name: 'Production',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
      ),
      color: '#74a6be'
    },
    {
      id: 'predictions',
      name: 'Cash Flow IA',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L3.5 15.49z"/>
        </svg>
      ),
      color: '#a7292e'
    },
    {
      id: 'analytics',
      name: 'Analytics',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
        </svg>
      ),
      color: '#74a6be'
    }
  ];

  return (
    <nav className="fixed left-0 top-0 h-full w-64 bg-black border-r border-white/20 z-40">
      {/* Logo Section */}
      <div className="p-6 border-b border-white/20">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl font-light" style={{color: '#74a6be'}}>E</span>
          <span className="text-2xl font-light" style={{color: '#74a6be'}}>Z</span>
          <span className="text-2xl font-light" style={{color: '#a7292e'}}>B</span>
          <span className="text-2xl font-light" style={{color: '#a7292e'}}>I</span>
        </div>
        <p className="text-sm font-light text-white/70">Analytics Dashboard</p>
      </div>

      {/* Navigation Tabs */}
      <div className="p-4 space-y-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`w-full flex items-center gap-4 p-4 font-light transition-all duration-300 hover:scale-105 ${
              activeTab === tab.id 
                ? 'border border-white/60 text-white' 
                : 'border border-white/20 text-white/70 hover:border-white/40 hover:text-white'
            }`}
            style={{backgroundColor: 'transparent'}}
          >
            <div style={{color: activeTab === tab.id ? tab.color : '#ffffff'}}>
              {tab.icon}
            </div>
            <span>{tab.name}</span>
          </button>
        ))}
      </div>

      {/* Data Sources Info */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/20">
        <div className="space-y-2 text-xs font-light text-white/60">
          <div className="flex justify-between">
            <span>PostgreSQL:</span>
            <span>203K+</span>
          </div>
          <div className="flex justify-between">
            <span>Excel Planning:</span>
            <span>Live</span>
          </div>
          <div className="flex justify-between">
            <span>Prédictions IA:</span>
            <span>ML</span>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default NavigationSidebar;