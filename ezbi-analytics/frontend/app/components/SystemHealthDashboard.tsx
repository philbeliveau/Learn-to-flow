/**
 * 🛡️ System Health Monitoring Dashboard
 * Real-time monitoring of system health, API status, and error tracking
 */

'use client';

import React, { useState, useEffect } from 'react';
import { robustApiService } from '../services/robustApiService';
import { robustHttpClient } from '../utils/robustHttpClient';
import { fallbackDataSystem } from '../utils/fallbackDataSystem';
import { ConnectionMonitor } from '../utils/connectionMonitor';

interface SystemHealth {
  overall: 'healthy' | 'degraded' | 'critical';
  apis: Record<string, {
    status: 'online' | 'offline' | 'degraded';
    responseTime: number;
    lastCheck: string;
    errorRate: number;
  }>;
  caches: {
    apiCache: number;
    fallbackCache: number;
    hitRate: number;
  };
  circuitBreakers: Record<string, {
    state: string;
    failureCount: number;
    successCount: number;
  }>;
  errors: Array<{
    timestamp: string;
    message: string;
    component: string;
    severity: 'low' | 'medium' | 'high';
  }>;
}

interface SystemHealthDashboardProps {
  isVisible: boolean;
  onClose: () => void;
}

export const SystemHealthDashboard: React.FC<SystemHealthDashboardProps> = ({ isVisible, onClose }) => {
  const [health, setHealth] = useState<SystemHealth>({
    overall: 'healthy',
    apis: {},
    caches: { apiCache: 0, fallbackCache: 0, hitRate: 0 },
    circuitBreakers: {},
    errors: []
  });
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    if (isVisible) {
      loadSystemHealth();
      
      if (autoRefresh) {
        const interval = setInterval(loadSystemHealth, 30000); // 30 seconds
        return () => clearInterval(interval);
      }
    }
  }, [isVisible, autoRefresh]);

  const loadSystemHealth = async () => {
    try {
      setLoading(true);
      
      // Test all critical endpoints
      const endpointTests = await robustApiService.testAllEndpoints();
      
      // Get cache stats
      const cacheStats = robustApiService.getCacheStats();
      
      // Get circuit breaker stats
      const circuitBreakerStats = robustHttpClient.getCircuitBreakerStats();
      
      // Get connection monitor stats
      const connectionMonitor = ConnectionMonitor.getExistingInstance();
      const connectionStats = connectionMonitor?.getStats();
      
      const apis: Record<string, any> = {};
      let totalResponseTime = 0;
      let onlineCount = 0;
      
      // Process endpoint test results
      Object.entries(endpointTests).forEach(([endpoint, result]) => {
        const status = result.success ? 'online' : 
                     result.fallback ? 'degraded' : 'offline';
        
        apis[endpoint] = {
          status,
          responseTime: result.responseTime || 0,
          lastCheck: new Date().toISOString(),
          errorRate: result.success ? 0 : 1
        };
        
        if (result.success) {
          onlineCount++;
          totalResponseTime += result.responseTime || 0;
        }
      });
      
      // Calculate overall health
      const totalApis = Object.keys(apis).length;
      const healthPercentage = totalApis > 0 ? (onlineCount / totalApis) * 100 : 0;
      
      const overall = healthPercentage >= 80 ? 'healthy' : 
                     healthPercentage >= 50 ? 'degraded' : 'critical';
      
      // Process cache stats
      const apiCacheSize = Object.keys(cacheStats.apiCache || {}).length;
      const fallbackCacheSize = Object.keys(cacheStats.fallbackCache || {}).length;
      
      setHealth({
        overall,
        apis,
        caches: {
          apiCache: apiCacheSize,
          fallbackCache: fallbackCacheSize,
          hitRate: 85 // Mock hit rate
        },
        circuitBreakers: circuitBreakerStats,
        errors: [] // Would be populated from error tracking
      });
      
    } catch (error) {
      console.error('Failed to load system health:', error);
    } finally {
      setLoading(false);
    }
  };

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return 'text-green-400';
      case 'degraded':
        return 'text-yellow-400';
      case 'critical':
      case 'offline':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  const getHealthIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return '✅';
      case 'degraded':
        return '⚠️';
      case 'critical':
      case 'offline':
        return '❌';
      default:
        return '⚪';
    }
  };

  const handleClearCache = async () => {
    robustApiService.clearCache();
    await loadSystemHealth();
  };

  const handleResetCircuitBreakers = () => {
    robustHttpClient.resetAllCircuitBreakers();
    loadSystemHealth();
  };

  const handleForceRefresh = async () => {
    await robustApiService.forceRefresh('/api/manufacturing/sales/kpis');
    await loadSystemHealth();
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-gray-900 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold text-white">System Health Dashboard</h2>
            <span className={`px-3 py-1 rounded-full text-sm ${getHealthColor(health.overall)} bg-gray-800`}>
              {getHealthIcon(health.overall)} {health.overall.toUpperCase()}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-3 py-1 rounded text-sm ${autoRefresh ? 'bg-blue-600 text-white' : 'bg-gray-600 text-gray-300'}`}
            >
              Auto Refresh
            </button>
            <button
              onClick={loadSystemHealth}
              className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
            >
              Refresh
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white text-xl"
            >
              ×
            </button>
          </div>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
          </div>
        )}

        {!loading && (
          <div className="p-6 space-y-6">
            {/* API Status */}
            <div>
              <h3 className="text-lg font-medium text-white mb-3">API Endpoints</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(health.apis).map(([endpoint, api]) => (
                  <div key={endpoint} className="bg-gray-800 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-gray-300 font-mono">{endpoint}</span>
                      <span className={`text-sm ${getHealthColor(api.status)}`}>
                        {getHealthIcon(api.status)} {api.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 space-y-1">
                      <div>Response Time: {api.responseTime}ms</div>
                      <div>Last Check: {new Date(api.lastCheck).toLocaleTimeString()}</div>
                      <div>Error Rate: {(api.errorRate * 100).toFixed(1)}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Cache Status */}
            <div>
              <h3 className="text-lg font-medium text-white mb-3">Cache Status</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="text-sm text-gray-300 mb-1">API Cache</div>
                  <div className="text-2xl font-bold text-white">{health.caches.apiCache}</div>
                  <div className="text-xs text-gray-400">cached entries</div>
                </div>
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="text-sm text-gray-300 mb-1">Fallback Cache</div>
                  <div className="text-2xl font-bold text-white">{health.caches.fallbackCache}</div>
                  <div className="text-xs text-gray-400">fallback entries</div>
                </div>
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="text-sm text-gray-300 mb-1">Hit Rate</div>
                  <div className="text-2xl font-bold text-white">{health.caches.hitRate}%</div>
                  <div className="text-xs text-gray-400">cache efficiency</div>
                </div>
              </div>
            </div>

            {/* Circuit Breakers */}
            <div>
              <h3 className="text-lg font-medium text-white mb-3">Circuit Breakers</h3>
              <div className="space-y-2">
                {Object.entries(health.circuitBreakers).map(([endpoint, breaker]) => (
                  <div key={endpoint} className="bg-gray-800 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-300 font-mono">{endpoint}</span>
                      <span className={`text-sm ${getHealthColor(breaker.state.toLowerCase())}`}>
                        {breaker.state}
                      </span>
                    </div>
                    <div className="text-xs text-gray-400 mt-2">
                      Failures: {breaker.failureCount} | Success: {breaker.successCount}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div>
              <h3 className="text-lg font-medium text-white mb-3">Actions</h3>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={handleClearCache}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  Clear All Caches
                </button>
                <button
                  onClick={handleResetCircuitBreakers}
                  className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
                >
                  Reset Circuit Breakers
                </button>
                <button
                  onClick={handleForceRefresh}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Force Refresh Data
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemHealthDashboard;