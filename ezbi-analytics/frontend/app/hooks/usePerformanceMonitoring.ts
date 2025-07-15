/**
 * Performance Monitoring Hook
 * Tracks loading times, cache hit rates, and user interactions
 * Performance Engineer Integration: Real-time metrics collection
 */

import { useState, useEffect, useCallback } from 'react';
import { cacheService } from '../services/cacheService';
import { authService } from '../services/authService';

interface PerformanceMetrics {
  pageLoadTime: number;
  apiResponseTimes: Record<string, number>;
  cacheHitRate: number;
  memoryUsage: number;
  renderTime: number;
  totalRequests: number;
  successfulRequests: number;
  errorRate: number;
}

interface PerformanceEvent {
  type: 'page_load' | 'api_call' | 'cache_hit' | 'cache_miss' | 'error' | 'user_action';
  timestamp: number;
  duration?: number;
  endpoint?: string;
  success?: boolean;
  metadata?: Record<string, any>;
}

export function usePerformanceMonitoring() {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    pageLoadTime: 0,
    apiResponseTimes: {},
    cacheHitRate: 0,
    memoryUsage: 0,
    renderTime: 0,
    totalRequests: 0,
    successfulRequests: 0,
    errorRate: 0
  });
  
  const [events, setEvents] = useState<PerformanceEvent[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(false);

  // Track page load time
  useEffect(() => {
    const startTime = performance.now();
    
    const handleLoad = () => {
      const loadTime = performance.now() - startTime;
      recordEvent({
        type: 'page_load',
        timestamp: Date.now(),
        duration: loadTime
      });
      
      setMetrics(prev => ({
        ...prev,
        pageLoadTime: loadTime
      }));
    };

    if (document.readyState === 'complete') {
      handleLoad();
    } else {
      window.addEventListener('load', handleLoad);
      return () => window.removeEventListener('load', handleLoad);
    }
  }, []);

  // Monitor memory usage
  useEffect(() => {
    const interval = setInterval(() => {
      if ('memory' in performance) {
        const memInfo = (performance as any).memory;
        const memoryUsage = memInfo.usedJSHeapSize / memInfo.totalJSHeapSize;
        
        setMetrics(prev => ({
          ...prev,
          memoryUsage: memoryUsage * 100
        }));
      }
    }, 5000); // Check every 5 seconds

    return () => clearInterval(interval);
  }, []);

  // Record performance events
  const recordEvent = useCallback((event: PerformanceEvent) => {
    setEvents(prev => [...prev.slice(-999), event]); // Keep last 1000 events
  }, []);

  // Track API calls
  const trackApiCall = useCallback(async <T>(
    endpoint: string,
    apiCall: () => Promise<T>,
    useCache: boolean = true
  ): Promise<T> => {
    const startTime = performance.now();
    const cacheKey = `api_${endpoint}`;
    
    try {
      let result!: T; // Definite assignment assertion
      let fromCache = false;
      
      // Check cache first if enabled
      if (useCache) {
        const cachedResult = await cacheService.get<T>(cacheKey);
        if (cachedResult !== null) {
          result = cachedResult;
          fromCache = true;
          
          recordEvent({
            type: 'cache_hit',
            timestamp: Date.now(),
            endpoint,
            duration: performance.now() - startTime
          });
        }
      }
      
      // Make API call if not cached
      if (!fromCache) {
        result = await apiCall();
        
        // Cache the result
        if (useCache) {
          await cacheService.set(cacheKey, result, 300); // 5 minutes default
        }
        
        recordEvent({
          type: 'cache_miss',
          timestamp: Date.now(),
          endpoint,
          duration: performance.now() - startTime
        });
      }
      
      
      const duration = performance.now() - startTime;
      
      recordEvent({
        type: 'api_call',
        timestamp: Date.now(),
        endpoint,
        duration,
        success: true,
        metadata: { fromCache }
      });
      
      // Update metrics
      setMetrics(prev => ({
        ...prev,
        apiResponseTimes: {
          ...prev.apiResponseTimes,
          [endpoint]: duration
        },
        totalRequests: prev.totalRequests + 1,
        successfulRequests: prev.successfulRequests + 1,
        errorRate: (prev.totalRequests - prev.successfulRequests) / (prev.totalRequests + 1) * 100
      }));
      
      return result;
    } catch (error) {
      const duration = performance.now() - startTime;
      
      recordEvent({
        type: 'error',
        timestamp: Date.now(),
        endpoint,
        duration,
        success: false,
        metadata: { error: error instanceof Error ? error.message : 'Unknown error' }
      });
      
      setMetrics(prev => ({
        ...prev,
        totalRequests: prev.totalRequests + 1,
        errorRate: (prev.totalRequests - prev.successfulRequests + 1) / (prev.totalRequests + 1) * 100
      }));
      
      throw error;
    }
  }, [recordEvent]);

  // Track render performance
  const trackRender = useCallback((componentName: string, renderFn: () => void) => {
    const startTime = performance.now();
    renderFn();
    const renderTime = performance.now() - startTime;
    
    recordEvent({
      type: 'user_action',
      timestamp: Date.now(),
      duration: renderTime,
      metadata: { action: 'render', component: componentName }
    });
    
    setMetrics(prev => ({
      ...prev,
      renderTime: Math.max(prev.renderTime, renderTime)
    }));
  }, [recordEvent]);

  // Track user actions
  const trackUserAction = useCallback((action: string, metadata?: Record<string, any>) => {
    recordEvent({
      type: 'user_action',
      timestamp: Date.now(),
      metadata: { action, ...metadata }
    });
  }, [recordEvent]);

  // Calculate cache hit rate
  useEffect(() => {
    const cacheHits = events.filter(e => e.type === 'cache_hit').length;
    const cacheMisses = events.filter(e => e.type === 'cache_miss').length;
    const totalCacheRequests = cacheHits + cacheMisses;
    
    if (totalCacheRequests > 0) {
      setMetrics(prev => ({
        ...prev,
        cacheHitRate: (cacheHits / totalCacheRequests) * 100
      }));
    }
  }, [events]);

  // Send metrics to backend
  const sendMetrics = useCallback(async () => {
    try {
      const headers = await authService.getAuthHeaders();
      await fetch('/api/v1/metrics/performance', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          metrics,
          events: events.slice(-100), // Send last 100 events
          timestamp: Date.now(),
          user_id: authService.getCurrentUser()?.id
        })
      });
    } catch (error) {
      console.error('Failed to send performance metrics:', error);
    }
  }, [metrics, events]);

  // Auto-send metrics every 30 seconds
  useEffect(() => {
    if (isMonitoring) {
      const interval = setInterval(sendMetrics, 30000);
      return () => clearInterval(interval);
    }
  }, [isMonitoring, sendMetrics]);

  // Get performance report
  const getPerformanceReport = useCallback(() => {
    const recentEvents = events.slice(-100);
    const avgResponseTime = Object.values(metrics.apiResponseTimes).reduce((a, b) => a + b, 0) / Object.keys(metrics.apiResponseTimes).length || 0;
    
    return {
      overview: {
        pageLoadTime: metrics.pageLoadTime,
        avgResponseTime,
        cacheHitRate: metrics.cacheHitRate,
        errorRate: metrics.errorRate,
        memoryUsage: metrics.memoryUsage
      },
      detailed: metrics,
      recentEvents,
      recommendations: generateRecommendations(metrics)
    };
  }, [metrics, events]);

  const generateRecommendations = (metrics: PerformanceMetrics): string[] => {
    const recommendations: string[] = [];
    
    if (metrics.pageLoadTime > 3000) {
      recommendations.push('Page load time is high. Consider optimizing bundle size or enabling code splitting.');
    }
    
    if (metrics.cacheHitRate < 70) {
      recommendations.push('Cache hit rate is low. Consider increasing cache TTL or improving cache strategy.');
    }
    
    if (metrics.errorRate > 5) {
      recommendations.push('Error rate is high. Check API endpoints and error handling.');
    }
    
    if (metrics.memoryUsage > 80) {
      recommendations.push('Memory usage is high. Consider optimizing component renders or data structures.');
    }
    
    const slowEndpoints = Object.entries(metrics.apiResponseTimes)
      .filter(([_, time]) => time > 2000)
      .map(([endpoint, _]) => endpoint);
    
    if (slowEndpoints.length > 0) {
      recommendations.push(`Slow API endpoints detected: ${slowEndpoints.join(', ')}. Consider optimization.`);
    }
    
    return recommendations;
  };

  return {
    metrics,
    events,
    isMonitoring,
    setIsMonitoring,
    trackApiCall,
    trackRender,
    trackUserAction,
    getPerformanceReport,
    sendMetrics
  };
}