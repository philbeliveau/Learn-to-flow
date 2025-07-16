'use client';

import React from 'react';
import { authService, UserRole, Permission } from '../services/authService';
import RoleGuard from './auth/RoleGuard';
import useSchedulerStatus from '../hooks/useSchedulerStatus';

interface NavigationTab {
  id: string;
  name: string;
  icon: JSX.Element;
  color: string;
  requiredPermissions?: Permission[];
  requiredRoles?: UserRole[];
  description?: string;
}

interface NavigationSidebarProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

const NavigationSidebar: React.FC<NavigationSidebarProps> = ({ activeTab, onTabChange }) => {
  const user = authService.getCurrentUser();
  const { status: schedulerStatus, loading: schedulerLoading, error: schedulerError } = useSchedulerStatus();
  
  const tabs: NavigationTab[] = [
    {
      id: 'overview',
      name: 'Dashboard',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>
        </svg>
      ),
      color: '#74a6be',
      requiredPermissions: [Permission.READ_DASHBOARD],
      description: 'Main dashboard overview'
    },
    {
      id: 'financial',
      name: 'Financial',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M7 15h2c0 1.08 1.37 2 3 2s3-.92 3-2c0-1.1-1.04-1.5-3.24-2.03C9.64 12.44 7 11.78 7 9c0-1.79 1.47-3.31 3.5-3.82V3h3v2.18C15.53 5.69 17 7.21 17 9h-2c0-1.08-1.37-2-3-2s-3 .92-3 2c0 1.1 1.04 1.5 3.24 2.03C14.36 11.56 17 12.22 17 15c0 1.79-1.47 3.31-3.5 3.82V21h-3v-2.18C8.47 18.31 7 16.79 7 15z"/>
        </svg>
      ),
      color: '#a7292e',
      requiredPermissions: [Permission.READ_FINANCE],
      description: 'Financial analysis and reporting'
    },
    {
      id: 'manufacturing',
      name: 'Manufacturing',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
      ),
      color: '#74a6be',
      requiredPermissions: [Permission.READ_MANUFACTURING],
      description: 'Production and operations data'
    },
    {
      id: 'manufacturing-bi',
      name: 'Manufacturing BI',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M2 3h6v4H2V3zm6 8H2v8h6v-8zm2-8h12v4H10V3zm12 6H10v2h12V9zm-12 4h12v8H10v-8z"/>
        </svg>
      ),
      color: '#a7292e',
      requiredPermissions: [Permission.READ_MANUFACTURING, Permission.READ_ANALYTICS],
      description: 'Advanced manufacturing analytics'
    },
    {
      id: 'predictions',
      name: 'AI Predictions',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M3.5 18.49l6-6.01 4 4L22 6.92l-1.41-1.41-7.09 7.97-4-4L3.5 15.49z"/>
        </svg>
      ),
      color: '#a7292e',
      requiredPermissions: [Permission.READ_ANALYTICS],
      requiredRoles: [UserRole.ANALYST, UserRole.MANAGER, UserRole.ADMIN],
      description: 'Machine learning predictions'
    },
    {
      id: 'analytics',
      name: 'Analytics',
      icon: (
        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
        </svg>
      ),
      color: '#74a6be',
      requiredPermissions: [Permission.READ_ANALYTICS],
      description: 'Advanced analytics and insights'
    }
  ];

  // Filter tabs based on user permissions
  const availableTabs = tabs.filter(tab => {
    if (tab.requiredPermissions && !authService.hasAnyPermission(tab.requiredPermissions)) {
      return false;
    }
    if (tab.requiredRoles && !authService.hasAnyRole(tab.requiredRoles)) {
      return false;
    }
    return true;
  });

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
        {availableTabs.map((tab) => (
          <RoleGuard 
            key={tab.id}
            requiredPermissions={tab.requiredPermissions}
            requiredRoles={tab.requiredRoles}
            showFallback={false}
          >
            <button
              onClick={() => onTabChange(tab.id)}
              className={`w-full flex items-center gap-4 p-4 font-light transition-all duration-300 hover:scale-105 group ${
                activeTab === tab.id 
                  ? 'border border-white/60 text-white bg-white/5' 
                  : 'border border-white/20 text-white/70 hover:border-white/40 hover:text-white hover:bg-white/5'
              }`}
              style={{backgroundColor: activeTab === tab.id ? 'rgba(255,255,255,0.05)' : 'transparent'}}
              title={tab.description}
            >
              <div style={{color: activeTab === tab.id ? tab.color : '#ffffff'}} className="transition-colors">
                {tab.icon}
              </div>
              <div className="flex-1">
                <span className="block text-left">{tab.name}</span>
                {tab.description && (
                  <span className="block text-xs text-white/40 mt-1 group-hover:text-white/60">
                    {tab.description}
                  </span>
                )}
              </div>
            </button>
          </RoleGuard>
        ))}
      </div>

      {/* User Info & Data Sources */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/20">
        {/* User Info */}
        <div className="mb-4 p-3 bg-white/5 rounded">
          <div className="text-xs font-light text-white/80">
            <div className="flex items-center gap-2 mb-1">
              <div className={`w-2 h-2 rounded-full ${
                user?.role === UserRole.ADMIN ? 'bg-red-400' :
                user?.role === UserRole.MANAGER ? 'bg-blue-400' :
                user?.role === UserRole.ANALYST ? 'bg-green-400' :
                'bg-gray-400'
              }`}></div>
              <span>{user?.name}</span>
            </div>
            <div className="text-white/60 text-xs">
              {user?.role?.toUpperCase()} • {user?.permissions?.length || 0} permissions
            </div>
          </div>
        </div>
        
        {/* Data Sources Info */}
        <div className="space-y-2 text-xs font-light text-white/60">
          <div className="flex justify-between">
            <span>PostgreSQL:</span>
            <span className="text-green-400">203K+</span>
          </div>
          <div className="flex justify-between">
            <span>Redis Cache:</span>
            <span className="text-blue-400">Active</span>
          </div>
          <div className="flex justify-between">
            <span>AI Predictions:</span>
            <span className="text-purple-400">ML</span>
          </div>
          <div className="flex justify-between">
            <span>Scheduler:</span>
            <span className={
              schedulerLoading ? 'text-yellow-400' :
              schedulerError ? 'text-red-400' :
              schedulerStatus?.running ? 'text-green-400' : 
              'text-gray-400'
            }>
              {schedulerLoading ? 'Loading...' :
               schedulerError ? 'Error' :
               schedulerStatus?.running ? `${schedulerStatus.jobs_count} Jobs` : 'Offline'}
            </span>
          </div>
          <div className="flex justify-between">
            <span>Security:</span>
            <span className={user?.is_mfa_enabled ? 'text-green-400' : 'text-yellow-400'}>
              {user?.is_mfa_enabled ? 'MFA' : 'Standard'}
            </span>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default NavigationSidebar;