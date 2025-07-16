/**
 * 🛡️ Robust HTTP Client with Advanced Error Handling
 * Implements retry logic, circuit breaker, and comprehensive error recovery
 */

import { authService } from '../services/authService';

export interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  retryableStatusCodes: number[];
  retryableErrors: string[];
}

export interface CircuitBreakerConfig {
  failureThreshold: number;
  resetTimeout: number;
  monitoringWindow: number;
}

export interface RequestConfig extends RequestInit {
  timeout?: number;
  retries?: Partial<RetryConfig>;
  circuitBreaker?: boolean;
  fallback?: any;
  skipAuth?: boolean;
}

export interface ApiError extends Error {
  status?: number;
  code?: string;
  response?: Response;
  retryCount?: number;
  isRetryable?: boolean;
}

export enum CircuitBreakerState {
  CLOSED = 'CLOSED',
  OPEN = 'OPEN',
  HALF_OPEN = 'HALF_OPEN'
}

class CircuitBreaker {
  private state: CircuitBreakerState = CircuitBreakerState.CLOSED;
  private failureCount = 0;
  private successCount = 0;
  private lastFailureTime = 0;
  private nextAttempt = 0;

  constructor(private config: CircuitBreakerConfig) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitBreakerState.OPEN) {
      if (Date.now() < this.nextAttempt) {
        throw new Error('Circuit breaker is OPEN');
      }
      this.state = CircuitBreakerState.HALF_OPEN;
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failureCount = 0;
    this.successCount++;
    
    if (this.state === CircuitBreakerState.HALF_OPEN) {
      this.state = CircuitBreakerState.CLOSED;
    }
  }

  private onFailure(): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    if (this.failureCount >= this.config.failureThreshold) {
      this.state = CircuitBreakerState.OPEN;
      this.nextAttempt = Date.now() + this.config.resetTimeout;
    }
  }

  getState(): CircuitBreakerState {
    return this.state;
  }

  getStats() {
    return {
      state: this.state,
      failureCount: this.failureCount,
      successCount: this.successCount,
      lastFailureTime: this.lastFailureTime,
      nextAttempt: this.nextAttempt
    };
  }
}

export class RobustHttpClient {
  private static instance: RobustHttpClient;
  private circuitBreakers: Map<string, CircuitBreaker> = new Map();
  private requestInterceptors: ((config: RequestConfig) => RequestConfig | Promise<RequestConfig>)[] = [];
  private responseInterceptors: ((response: Response) => Response | Promise<Response>)[] = [];
  private errorInterceptors: ((error: ApiError) => ApiError | Promise<ApiError>)[] = [];

  private readonly defaultRetryConfig: RetryConfig = {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 10000,
    backoffMultiplier: 2,
    retryableStatusCodes: [408, 429, 500, 502, 503, 504],
    retryableErrors: ['NetworkError', 'TimeoutError', 'AbortError']
  };

  private readonly defaultCircuitBreakerConfig: CircuitBreakerConfig = {
    failureThreshold: 5,
    resetTimeout: 30000,
    monitoringWindow: 60000
  };

  private constructor() {}

  static getInstance(): RobustHttpClient {
    if (!RobustHttpClient.instance) {
      RobustHttpClient.instance = new RobustHttpClient();
    }
    return RobustHttpClient.instance;
  }

  /**
   * Add request interceptor
   */
  addRequestInterceptor(interceptor: (config: RequestConfig) => RequestConfig | Promise<RequestConfig>) {
    this.requestInterceptors.push(interceptor);
  }

  /**
   * Add response interceptor
   */
  addResponseInterceptor(interceptor: (response: Response) => Response | Promise<Response>) {
    this.responseInterceptors.push(interceptor);
  }

  /**
   * Add error interceptor
   */
  addErrorInterceptor(interceptor: (error: ApiError) => ApiError | Promise<ApiError>) {
    this.errorInterceptors.push(interceptor);
  }

  /**
   * Main request method with comprehensive error handling
   */
  async request<T>(url: string, config: RequestConfig = {}): Promise<T> {
    const startTime = Date.now();
    const requestId = this.generateRequestId();
    
    try {
      // Apply request interceptors
      let processedConfig = config;
      for (const interceptor of this.requestInterceptors) {
        processedConfig = await interceptor(processedConfig);
      }

      // Get circuit breaker for this endpoint
      const circuitBreaker = this.getCircuitBreaker(url);
      
      // Execute request with circuit breaker
      const response = await circuitBreaker.execute(async () => {
        return await this.executeRequest(url, processedConfig, requestId);
      });

      // Apply response interceptors
      let processedResponse = response;
      for (const interceptor of this.responseInterceptors) {
        processedResponse = await interceptor(processedResponse);
      }

      const data = await this.parseResponse<T>(processedResponse);
      
      this.logRequest(requestId, url, config, Date.now() - startTime, 'success');
      return data;

    } catch (error) {
      let processedError = error as ApiError;
      
      // Apply error interceptors
      for (const interceptor of this.errorInterceptors) {
        processedError = await interceptor(processedError);
      }

      this.logRequest(requestId, url, config, Date.now() - startTime, 'error', processedError);
      
      // Return fallback if available
      if (config.fallback !== undefined) {
        console.warn(`[RobustHttpClient] Returning fallback data for ${url}`);
        return config.fallback;
      }

      throw processedError;
    }
  }

  /**
   * Execute request with retry logic
   */
  private async executeRequest(url: string, config: RequestConfig, requestId: string): Promise<Response> {
    const retryConfig = { ...this.defaultRetryConfig, ...config.retries };
    let lastError: ApiError;

    for (let attempt = 0; attempt <= retryConfig.maxRetries; attempt++) {
      try {
        const response = await this.makeRequest(url, config, requestId, attempt);
        
        if (response.ok) {
          return response;
        }

        // Check if status code is retryable
        if (!retryConfig.retryableStatusCodes.includes(response.status)) {
          throw this.createApiError(
            `HTTP ${response.status}: ${response.statusText}`,
            response.status,
            response,
            attempt,
            false
          );
        }

        throw this.createApiError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          response,
          attempt,
          true
        );

      } catch (error) {
        lastError = this.processError(error, attempt, retryConfig);
        
        if (!lastError.isRetryable || attempt === retryConfig.maxRetries) {
          throw lastError;
        }

        // Calculate delay with exponential backoff
        const delay = Math.min(
          retryConfig.baseDelay * Math.pow(retryConfig.backoffMultiplier, attempt),
          retryConfig.maxDelay
        );

        console.warn(`[RobustHttpClient] Retry ${attempt + 1}/${retryConfig.maxRetries} for ${url} in ${delay}ms`);
        await this.delay(delay);
      }
    }

    throw lastError!;
  }

  /**
   * Make individual HTTP request
   */
  private async makeRequest(url: string, config: RequestConfig, requestId: string, attempt: number): Promise<Response> {
    const timeout = config.timeout || 10000;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      // Prepare headers
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        'X-Request-ID': requestId,
        'X-Retry-Attempt': attempt.toString(),
        ...config.headers
      };

      // Add authentication if not skipped
      if (!config.skipAuth) {
        const authHeaders = await authService.getAuthHeaders();
        Object.assign(headers, authHeaders);
      }

      const response = await fetch(url, {
        ...config,
        headers,
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      return response;

    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  /**
   * Parse response based on content type
   */
  private async parseResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get('content-type') || '';
    
    if (contentType.includes('application/json')) {
      return await response.json();
    } else if (contentType.includes('text/')) {
      return await response.text() as unknown as T;
    } else {
      return await response.blob() as unknown as T;
    }
  }

  /**
   * Process and classify errors
   */
  private processError(error: any, attempt: number, retryConfig: RetryConfig): ApiError {
    let isRetryable = false;
    let code = 'UnknownError';
    let message = 'Unknown error occurred';

    if (error.name === 'AbortError') {
      code = 'TimeoutError';
      message = 'Request timed out';
      isRetryable = true;
    } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
      code = 'NetworkError';
      message = 'Network connection failed';
      isRetryable = true;
    } else if (error instanceof Error) {
      code = error.name;
      message = error.message;
      isRetryable = retryConfig.retryableErrors.includes(error.name);
    }

    return this.createApiError(message, undefined, undefined, attempt, isRetryable, code);
  }

  /**
   * Create standardized API error
   */
  private createApiError(
    message: string,
    status?: number,
    response?: Response,
    retryCount?: number,
    isRetryable?: boolean,
    code?: string
  ): ApiError {
    const error = new Error(message) as ApiError;
    error.name = 'ApiError';
    error.status = status;
    error.response = response;
    error.retryCount = retryCount;
    error.isRetryable = isRetryable;
    error.code = code;
    return error;
  }

  /**
   * Get or create circuit breaker for endpoint
   */
  private getCircuitBreaker(url: string): CircuitBreaker {
    const key = this.getCircuitBreakerKey(url);
    
    if (!this.circuitBreakers.has(key)) {
      this.circuitBreakers.set(key, new CircuitBreaker(this.defaultCircuitBreakerConfig));
    }
    
    return this.circuitBreakers.get(key)!;
  }

  /**
   * Generate circuit breaker key from URL
   */
  private getCircuitBreakerKey(url: string): string {
    try {
      const urlObj = new URL(url);
      return `${urlObj.origin}${urlObj.pathname}`;
    } catch {
      return url;
    }
  }

  /**
   * Generate unique request ID
   */
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Delay helper
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Log request details
   */
  private logRequest(
    requestId: string,
    url: string,
    config: RequestConfig,
    duration: number,
    status: 'success' | 'error',
    error?: ApiError
  ): void {
    const logData = {
      requestId,
      url,
      method: config.method || 'GET',
      duration,
      status,
      timestamp: new Date().toISOString(),
      error: error ? {
        message: error.message,
        status: error.status,
        code: error.code,
        retryCount: error.retryCount,
        isRetryable: error.isRetryable
      } : undefined
    };

    if (status === 'error') {
      console.error('[RobustHttpClient] Request failed:', logData);
    } else {
      console.log('[RobustHttpClient] Request succeeded:', logData);
    }
  }

  /**
   * Get circuit breaker stats
   */
  getCircuitBreakerStats(): Record<string, any> {
    const stats: Record<string, any> = {};
    
    this.circuitBreakers.forEach((breaker, key) => {
      stats[key] = breaker.getStats();
    });
    
    return stats;
  }

  /**
   * Reset circuit breaker
   */
  resetCircuitBreaker(url: string): void {
    const key = this.getCircuitBreakerKey(url);
    this.circuitBreakers.delete(key);
  }

  /**
   * Reset all circuit breakers
   */
  resetAllCircuitBreakers(): void {
    this.circuitBreakers.clear();
  }
}

// Export singleton instance
export const robustHttpClient = RobustHttpClient.getInstance();

// Convenience methods
export const robustFetch = {
  get: <T>(url: string, config?: RequestConfig) => 
    robustHttpClient.request<T>(url, { ...config, method: 'GET' }),
  
  post: <T>(url: string, data?: any, config?: RequestConfig) => 
    robustHttpClient.request<T>(url, { 
      ...config, 
      method: 'POST', 
      body: JSON.stringify(data) 
    }),
  
  put: <T>(url: string, data?: any, config?: RequestConfig) => 
    robustHttpClient.request<T>(url, { 
      ...config, 
      method: 'PUT', 
      body: JSON.stringify(data) 
    }),
  
  delete: <T>(url: string, config?: RequestConfig) => 
    robustHttpClient.request<T>(url, { ...config, method: 'DELETE' })
};