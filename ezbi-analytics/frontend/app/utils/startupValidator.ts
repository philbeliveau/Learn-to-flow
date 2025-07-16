/**
 * Startup Validation System
 * Validates all required services and configuration before showing the UI
 */

export interface StartupCheckResult {
  name: string;
  status: 'success' | 'warning' | 'error';
  message: string;
  details?: any;
  fix?: string;
}

export interface StartupValidationResult {
  isValid: boolean;
  checks: StartupCheckResult[];
  errors: number;
  warnings: number;
  summary: string;
}

export class StartupValidator {
  private static readonly REQUIRED_SERVICES = [
    'backend-api',
    'environment-vars',
    'auth-service',
    'browser-compatibility'
  ];

  /**
   * Run all startup validation checks
   */
  public static async validateStartup(): Promise<StartupValidationResult> {
    const checks: StartupCheckResult[] = [];
    
    console.log('🚀 Starting system validation...');
    
    // Run all validation checks
    checks.push(await this.checkEnvironmentVariables());
    checks.push(await this.checkBackendAPI());
    checks.push(await this.checkAuthService());
    checks.push(await this.checkBrowserCompatibility());
    checks.push(await this.checkLocalStorage());
    checks.push(await this.checkNetworkConnectivity());
    
    // Calculate summary
    const errors = checks.filter(c => c.status === 'error').length;
    const warnings = checks.filter(c => c.status === 'warning').length;
    const isValid = errors === 0;
    
    const summary = this.generateSummary(checks);
    
    return {
      isValid,
      checks,
      errors,
      warnings,
      summary
    };
  }

  /**
   * Check environment variables
   */
  private static async checkEnvironmentVariables(): Promise<StartupCheckResult> {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      
      if (!apiUrl) {
        return {
          name: 'Environment Variables',
          status: 'warning',
          message: 'API URL not configured, using default',
          details: { defaultUrl: 'http://localhost:8000' },
          fix: 'Set NEXT_PUBLIC_API_URL in .env.local'
        };
      }
      
      // Validate URL format
      try {
        new URL(apiUrl);
      } catch {
        return {
          name: 'Environment Variables',
          status: 'error',
          message: 'Invalid API URL format',
          details: { apiUrl },
          fix: 'Fix NEXT_PUBLIC_API_URL format in .env.local'
        };
      }
      
      return {
        name: 'Environment Variables',
        status: 'success',
        message: 'Environment variables configured correctly',
        details: { apiUrl }
      };
    } catch (error) {
      return {
        name: 'Environment Variables',
        status: 'error',
        message: 'Failed to check environment variables',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      };
    }
  }

  /**
   * Check backend API availability
   */
  private static async checkBackendAPI(): Promise<StartupCheckResult> {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      const response = await fetch(`${apiUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000)
      });
      
      if (!response.ok) {
        return {
          name: 'Backend API',
          status: 'error',
          message: `Backend API returned ${response.status}`,
          details: { status: response.status, statusText: response.statusText },
          fix: 'Ensure backend server is running with `python run.py`'
        };
      }
      
      const data = await response.json();
      
      if (!data.service || !data.service.includes('EZBI')) {
        return {
          name: 'Backend API',
          status: 'warning',
          message: 'Backend API response format unexpected',
          details: { response: data },
          fix: 'Verify backend is running the correct EZBI service'
        };
      }
      
      return {
        name: 'Backend API',
        status: 'success',
        message: 'Backend API is healthy and responding',
        details: { service: data.service, status: data.status }
      };
    } catch (error) {
      return {
        name: 'Backend API',
        status: 'error',
        message: 'Cannot connect to backend API',
        details: { error: error instanceof Error ? error.message : 'Unknown error' },
        fix: 'Start backend server with `python run.py` and check port configuration'
      };
    }
  }

  /**
   * Check authentication service
   */
  private static async checkAuthService(): Promise<StartupCheckResult> {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      // Test auth endpoint with OPTIONS request (CORS preflight)
      const response = await fetch(`${apiUrl}/api/v1/auth/login`, {
        method: 'OPTIONS',
        headers: {
          'Origin': window.location.origin,
          'Access-Control-Request-Method': 'POST',
          'Access-Control-Request-Headers': 'Content-Type'
        },
        signal: AbortSignal.timeout(5000)
      });
      
      if (!response.ok) {
        return {
          name: 'Authentication Service',
          status: 'error',
          message: 'Authentication endpoint not accessible',
          details: { status: response.status },
          fix: 'Check backend authentication configuration'
        };
      }
      
      // Check CORS headers
      const corsHeaders = {
        'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
        'access-control-allow-methods': response.headers.get('access-control-allow-methods'),
        'access-control-allow-headers': response.headers.get('access-control-allow-headers')
      };
      
      if (!corsHeaders['access-control-allow-origin']) {
        return {
          name: 'Authentication Service',
          status: 'warning',
          message: 'CORS configuration may cause issues',
          details: { corsHeaders },
          fix: 'Verify CORS settings in backend configuration'
        };
      }
      
      return {
        name: 'Authentication Service',
        status: 'success',
        message: 'Authentication service is accessible',
        details: { corsHeaders }
      };
    } catch (error) {
      return {
        name: 'Authentication Service',
        status: 'error',
        message: 'Authentication service check failed',
        details: { error: error instanceof Error ? error.message : 'Unknown error' },
        fix: 'Ensure authentication endpoints are configured correctly'
      };
    }
  }

  /**
   * Check browser compatibility
   */
  private static async checkBrowserCompatibility(): Promise<StartupCheckResult> {
    try {
      const issues: string[] = [];
      
      // Check for required APIs
      if (!window.fetch) {
        issues.push('fetch API not available');
      }
      
      if (!window.localStorage) {
        issues.push('localStorage not available');
      }
      
      if (!window.AbortController) {
        issues.push('AbortController not available');
      }
      
      if (!window.URL) {
        issues.push('URL API not available');
      }
      
      if (issues.length > 0) {
        return {
          name: 'Browser Compatibility',
          status: 'error',
          message: 'Browser lacks required features',
          details: { issues },
          fix: 'Use a modern browser (Chrome 60+, Firefox 57+, Safari 11+)'
        };
      }
      
      return {
        name: 'Browser Compatibility',
        status: 'success',
        message: 'Browser supports all required features',
        details: { userAgent: navigator.userAgent }
      };
    } catch (error) {
      return {
        name: 'Browser Compatibility',
        status: 'error',
        message: 'Browser compatibility check failed',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      };
    }
  }

  /**
   * Check localStorage functionality
   */
  private static async checkLocalStorage(): Promise<StartupCheckResult> {
    try {
      const testKey = 'ezbi-startup-test';
      const testValue = 'test-value';
      
      // Test write
      localStorage.setItem(testKey, testValue);
      
      // Test read
      const readValue = localStorage.getItem(testKey);
      
      // Test delete
      localStorage.removeItem(testKey);
      
      if (readValue !== testValue) {
        return {
          name: 'Local Storage',
          status: 'error',
          message: 'localStorage read/write failed',
          fix: 'Enable localStorage in browser settings'
        };
      }
      
      return {
        name: 'Local Storage',
        status: 'success',
        message: 'localStorage is working correctly'
      };
    } catch (error) {
      return {
        name: 'Local Storage',
        status: 'error',
        message: 'localStorage is not available',
        details: { error: error instanceof Error ? error.message : 'Unknown error' },
        fix: 'Enable localStorage in browser settings or use incognito mode'
      };
    }
  }

  /**
   * Check network connectivity
   */
  private static async checkNetworkConnectivity(): Promise<StartupCheckResult> {
    try {
      if (!navigator.onLine) {
        return {
          name: 'Network Connectivity',
          status: 'warning',
          message: 'Browser reports offline status',
          fix: 'Check internet connection'
        };
      }
      
      return {
        name: 'Network Connectivity',
        status: 'success',
        message: 'Network connectivity available'
      };
    } catch (error) {
      return {
        name: 'Network Connectivity',
        status: 'error',
        message: 'Network connectivity check failed',
        details: { error: error instanceof Error ? error.message : 'Unknown error' }
      };
    }
  }

  /**
   * Generate summary message
   */
  private static generateSummary(checks: StartupCheckResult[]): string {
    const total = checks.length;
    const successful = checks.filter(c => c.status === 'success').length;
    const warnings = checks.filter(c => c.status === 'warning').length;
    const errors = checks.filter(c => c.status === 'error').length;
    
    if (errors > 0) {
      return `❌ System validation failed: ${errors} error(s), ${warnings} warning(s) out of ${total} checks`;
    } else if (warnings > 0) {
      return `⚠️ System validation passed with warnings: ${warnings} warning(s) out of ${total} checks`;
    } else {
      return `✅ System validation passed: All ${total} checks successful`;
    }
  }

  /**
   * Get quick health status
   */
  public static async getQuickHealthStatus(): Promise<{ healthy: boolean; issues: string[] }> {
    const result = await this.validateStartup();
    
    return {
      healthy: result.isValid,
      issues: result.checks
        .filter(c => c.status === 'error')
        .map(c => c.message)
    };
  }
}