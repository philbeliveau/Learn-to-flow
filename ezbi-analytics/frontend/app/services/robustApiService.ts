/**
 * 🛡️ Robust API Service
 * Wraps all API calls with comprehensive error handling and fallback systems
 */

import { robustHttpClient, robustFetch } from '../utils/robustHttpClient';
import { fallbackDataSystem, setupDefaultFallbacks } from '../utils/fallbackDataSystem';
import { authService } from './authService';

export interface ApiOptions {
  timeout?: number;
  retries?: number;
  useCache?: boolean;
  cacheTTL?: number;
  useFallback?: boolean;
  fallbackData?: any;
  requireAuth?: boolean;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  statusCode?: number;
  cached?: boolean;
  fallback?: boolean;
  retryCount?: number;
  responseTime?: number;
}

export class RobustApiService {
  private static instance: RobustApiService;
  private apiBaseUrl: string;
  private cache: Map<string, { data: any; timestamp: number; ttl: number }> = new Map();

  private constructor() {
    this.apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    this.setupInterceptors();
    setupDefaultFallbacks();
  }

  static getInstance(): RobustApiService {
    if (!RobustApiService.instance) {
      RobustApiService.instance = new RobustApiService();
    }
    return RobustApiService.instance;
  }

  /**
   * Setup HTTP interceptors for automatic fallback handling
   */
  private setupInterceptors(): void {
    // Request interceptor
    robustHttpClient.addRequestInterceptor((config) => {
      console.log(`[RobustApiService] Making request: ${config.method || 'GET'} ${config.url || 'unknown'}`);
      return config;
    });

    // Response interceptor
    robustHttpClient.addResponseInterceptor((response) => {
      if (response.ok) {
        console.log(`[RobustApiService] Response success: ${response.status}`);
      }
      return response;
    });

    // Error interceptor
    robustHttpClient.addErrorInterceptor((error) => {
      console.error(`[RobustApiService] Request error:`, error);
      return error;
    });
  }

  /**
   * Generic API call with comprehensive error handling
   */
  async apiCall<T>(
    endpoint: string,
    options: ApiOptions = {}
  ): Promise<ApiResponse<T>> {
    const startTime = Date.now();
    const cacheKey = `${endpoint}_${JSON.stringify(options)}`;

    // Check cache first
    if (options.useCache && this.cache.has(cacheKey)) {
      const cached = this.cache.get(cacheKey)!;
      if (Date.now() - cached.timestamp < cached.ttl) {
        return {
          success: true,
          data: cached.data,
          cached: true,
          responseTime: Date.now() - startTime
        };
      }
    }

    const url = `${this.apiBaseUrl}${endpoint}`;
    
    try {
      const response = await robustHttpClient.request<T>(url, {
        timeout: options.timeout || 10000,
        retries: {
          maxRetries: options.retries || 3
        },
        fallback: options.useFallback ? 
          fallbackDataSystem.getFallbackData(endpoint) : 
          options.fallbackData,
        skipAuth: !options.requireAuth
      });

      // Store successful response for fallback
      if (options.useFallback) {
        fallbackDataSystem.storeSuccessfulResponse(endpoint, response);
      }

      // Cache successful response
      if (options.useCache) {
        this.cache.set(cacheKey, {
          data: response,
          timestamp: Date.now(),
          ttl: options.cacheTTL || 5 * 60 * 1000 // 5 minutes default
        });
      }

      return {
        success: true,
        data: response,
        responseTime: Date.now() - startTime
      };

    } catch (error: any) {
      console.error(`[RobustApiService] API call failed for ${endpoint}:`, error);

      // Try to return fallback data
      if (options.useFallback) {
        const fallbackData = fallbackDataSystem.getFallbackData(endpoint);
        if (fallbackData) {
          return {
            success: true,
            data: fallbackData,
            fallback: true,
            error: error.message,
            responseTime: Date.now() - startTime
          };
        }
      }

      // Return custom fallback data
      if (options.fallbackData) {
        return {
          success: true,
          data: options.fallbackData,
          fallback: true,
          error: error.message,
          responseTime: Date.now() - startTime
        };
      }

      // Return error response
      return {
        success: false,
        error: error.message,
        statusCode: error.status,
        retryCount: error.retryCount,
        responseTime: Date.now() - startTime
      };
    }
  }

  /**
   * Manufacturing API Methods
   */

  async getSalesKPIs(): Promise<ApiResponse<any>> {
    return this.apiCall('/api/manufacturing/sales/kpis', {
      useCache: true,
      cacheTTL: 5 * 60 * 1000, // 5 minutes
      useFallback: true,
      requireAuth: true
    });
  }

  async getOperationsData(): Promise<ApiResponse<any>> {
    return this.apiCall('/api/manufacturing/operations/products', {
      useCache: true,
      cacheTTL: 5 * 60 * 1000, // 5 minutes
      useFallback: true,
      requireAuth: true
    });
  }

  async getFinanceData(): Promise<ApiResponse<any>> {
    return this.apiCall('/api/manufacturing/finance/summary', {
      useCache: true,
      cacheTTL: 5 * 60 * 1000, // 5 minutes
      useFallback: true,
      requireAuth: true
    });
  }

  async getHRData(): Promise<ApiResponse<any>> {
    return this.apiCall('/api/manufacturing/hr/overview', {
      useCache: true,
      cacheTTL: 10 * 60 * 1000, // 10 minutes
      useFallback: true,
      requireAuth: true
    });
  }

  async getExpensesData(): Promise<ApiResponse<any>> {
    return this.apiCall('/api/manufacturing/expenses/analysis', {
      useCache: true,
      cacheTTL: 15 * 60 * 1000, // 15 minutes
      useFallback: true,
      requireAuth: true
    });
  }

  async getManufacturingDashboard(): Promise<ApiResponse<any>> {
    return this.apiCall('/api/v1/analytics/manufacturing-dashboard', {
      useCache: true,
      cacheTTL: 2 * 60 * 1000, // 2 minutes
      useFallback: true,
      requireAuth: true
    });
  }

  async getCompanyKPIs(): Promise<ApiResponse<any>> {
    return this.apiCall('/api/v1/company/kpis', {
      useCache: true,
      cacheTTL: 5 * 60 * 1000, // 5 minutes
      useFallback: true,
      requireAuth: true,
      fallbackData: {
        success: true,
        fallback: true,
        production: {
          efficiency: 0.85,
          capacity_utilization: 0.78,
          units_produced: 1200,
          defect_rate: 0.03
        },
        financial: {
          revenue_ytd: 1800000,
          expenses_ytd: 1350000,
          margin: 0.25,
          cash_position: 450000,
          liquidity_ratio: 2.1,
          working_capital: 270000,
          collection_period: 45,
          gross_margin: 0.35,
          roe: 0.15,
          roi: 0.12,
          revenue_growth: 0.08,
          ebitda_growth: 0.12,
          cash_flow_growth: 0.06
        },
        inventory: {
          turnover_ratio: 8.5,
          days_on_hand: 43,
          raw_materials: 125000,
          finished_goods: 89000
        },
        period: '2024-Q3',
        currency: 'EUR',
        timestamp: new Date().toISOString()
      }
    });
  }

  /**
   * Cash Flow API Methods
   */

  async getCurrentCashPosition(): Promise<ApiResponse<any>> {
    return this.apiCall('/api/v1/current-cash-position', {
      useCache: true,
      cacheTTL: 1 * 60 * 1000, // 1 minute
      useFallback: true,
      requireAuth: true,
      fallbackData: {
        success: true,
        fallback: true,
        current_position: {
          cash_balance: 847392.45,
          outstanding_receivables: 325000.00,
          outstanding_payables: 189000.00,
          net_working_capital: 983392.45,
          last_updated: new Date().toISOString().split('T')[0]
        },
        today_activity: {
          inflows: 45000.00,
          outflows: 32000.00,
          net_flow: 13000.00
        },
        metadata: {
          currency: 'EUR',
          company: 'Manufacture Lyonnaise SA',
          data_source: 'Fallback Data'
        },
        timestamp: new Date().toISOString()
      }
    });
  }

  async getCashFlowPrediction(days: number = 30): Promise<ApiResponse<any>> {
    return this.apiCall(`/api/v1/quick-prediction?days=${days}`, {
      useCache: true,
      cacheTTL: 3 * 60 * 1000, // 3 minutes
      useFallback: true,
      requireAuth: true,
      fallbackData: {
        success: true,
        fallback: true,
        summary: {
          total_predicted_inflows: 45000.00 * days,
          total_predicted_outflows: 32000.00 * days,
          net_cash_flow: 13000.00 * days,
          ending_balance: 847392.45 + (13000.00 * days),
          period_days: days,
          daily_average: 13000.00
        },
        period: `${days} days`,
        confidence: 0.78,
        risk_factors: [
          'Seasonal variations in Q4',
          'Customer payment delays',
          'Raw material cost volatility'
        ],
        key_insights: [
          `Positive cash flow trend: +€${13000.00}/day`,
          'Receivables collection improving',
          'Working capital optimized'
        ],
        metadata: {
          model_version: 'v2.0',
          currency: 'EUR',
          data_source: 'Fallback Analytics',
          generated_at: new Date().toISOString()
        },
        timestamp: new Date().toISOString()
      }
    });
  }

  async getBusinessPlanningStatus(): Promise<ApiResponse<any>> {
    return this.apiCall('/api/v1/business-planning-status', {
      useCache: true,
      cacheTTL: 10 * 60 * 1000, // 10 minutes
      useFallback: true,
      requireAuth: true
    });
  }

  /**
   * Health Check Methods
   */

  async healthCheck(): Promise<ApiResponse<any>> {
    return this.apiCall('/health', {
      timeout: 5000,
      retries: 1,
      requireAuth: false,
      fallbackData: {
        status: 'unavailable',
        timestamp: new Date().toISOString(),
        message: 'Health check failed - service may be down'
      }
    });
  }

  async getSchedulerStatus(): Promise<ApiResponse<any>> {
    return this.apiCall('/api/scheduler/status', {
      timeout: 3000,
      retries: 1,
      requireAuth: false,
      fallbackData: {
        running: false,
        jobs_count: 0,
        last_run: null,
        status: 'unavailable'
      }
    });
  }

  /**
   * Utility Methods
   */

  /**
   * Clear all caches
   */
  clearCache(): void {
    this.cache.clear();
    fallbackDataSystem.clearCache();
    console.log('✅ All caches cleared');
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): Record<string, any> {
    const stats: Record<string, any> = {
      apiCache: {},
      fallbackCache: fallbackDataSystem.getCacheStats(),
      circuitBreakers: robustHttpClient.getCircuitBreakerStats()
    };

    this.cache.forEach((cache, key) => {
      stats.apiCache[key] = {
        timestamp: cache.timestamp,
        age: Date.now() - cache.timestamp,
        ttl: cache.ttl,
        size: JSON.stringify(cache.data).length
      };
    });

    return stats;
  }

  /**
   * Force refresh endpoint data
   */
  async forceRefresh(endpoint: string): Promise<ApiResponse<any>> {
    // Clear cache for this endpoint
    const cacheKeys = Array.from(this.cache.keys()).filter(key => key.startsWith(endpoint));
    cacheKeys.forEach(key => this.cache.delete(key));

    // Reset circuit breaker
    robustHttpClient.resetCircuitBreaker(`${this.apiBaseUrl}${endpoint}`);

    // Make fresh request
    return this.apiCall(endpoint, {
      useCache: false,
      useFallback: false,
      requireAuth: true
    });
  }

  /**
   * Batch API calls with automatic retry and fallback
   */
  async batchApiCall(endpoints: string[], options: ApiOptions = {}): Promise<Record<string, ApiResponse<any>>> {
    const results: Record<string, ApiResponse<any>> = {};
    
    const promises = endpoints.map(async (endpoint) => {
      const result = await this.apiCall(endpoint, options);
      results[endpoint] = result;
    });

    await Promise.allSettled(promises);
    return results;
  }

  /**
   * Test all critical endpoints
   */
  async testAllEndpoints(): Promise<Record<string, ApiResponse<any>>> {
    const criticalEndpoints = [
      '/health',
      '/api/manufacturing/sales/kpis',
      '/api/manufacturing/operations/products',
      '/api/manufacturing/finance/summary',
      '/api/v1/company/kpis'
    ];

    console.log('🔍 Testing all critical endpoints...');
    return this.batchApiCall(criticalEndpoints, {
      timeout: 5000,
      retries: 1,
      useFallback: true,
      requireAuth: true
    });
  }
}

// Export singleton instance
export const robustApiService = RobustApiService.getInstance();