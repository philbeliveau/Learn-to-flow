/**
 * Environment Variable Validation System
 * Prevents configuration issues like the port 8003 vs 8000 problem
 */

export interface EnvValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
  detectedBackendPort?: number;
}

export interface SystemHealthCheck {
  apiUrl: string;
  isReachable: boolean;
  responseTime?: number;
  error?: string;
}

export class EnvironmentValidator {
  private static readonly REQUIRED_VARS = [
    'NEXT_PUBLIC_API_URL'
  ];

  private static readonly COMMON_BACKEND_PORTS = [8000, 8001, 8002, 8003, 8004, 8080, 3001];

  /**
   * Validate environment variables and configuration
   */
  public static async validateEnvironment(): Promise<EnvValidationResult> {
    const errors: string[] = [];
    const warnings: string[] = [];
    const suggestions: string[] = [];

    // Check required environment variables
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    // Parse API URL
    let parsedUrl: URL;
    try {
      parsedUrl = new URL(apiUrl);
    } catch (error) {
      errors.push(`Invalid API URL format: ${apiUrl}`);
      return { isValid: false, errors, warnings, suggestions };
    }

    // Check if API URL is localhost (expected for development)
    if (parsedUrl.hostname !== 'localhost' && parsedUrl.hostname !== '127.0.0.1') {
      warnings.push(`API URL is not localhost: ${parsedUrl.hostname}`);
    }

    // Check if API is reachable
    const healthCheck = await this.checkApiHealth(apiUrl);
    
    if (!healthCheck.isReachable) {
      errors.push(`Backend API is not reachable at ${apiUrl}`);
      
      // Try to detect the correct port
      const detectedPort = await this.detectBackendPort();
      if (detectedPort && detectedPort !== parseInt(parsedUrl.port)) {
        suggestions.push(`Backend appears to be running on port ${detectedPort}. Update NEXT_PUBLIC_API_URL to http://localhost:${detectedPort}`);
      }
    } else {
      // Backend is reachable, check response time
      if (healthCheck.responseTime && healthCheck.responseTime > 2000) {
        warnings.push(`Backend response time is slow: ${healthCheck.responseTime}ms`);
      }
    }

    // Check environment consistency
    const nodeEnv = process.env.NODE_ENV;
    if (nodeEnv === 'production' && parsedUrl.hostname === 'localhost') {
      warnings.push('Production environment detected with localhost API URL');
    }

    const isValid = errors.length === 0;
    
    return {
      isValid,
      errors,
      warnings,
      suggestions,
      detectedBackendPort: await this.detectBackendPort()
    };
  }

  /**
   * Check if API is healthy and reachable
   */
  private static async checkApiHealth(apiUrl: string): Promise<SystemHealthCheck> {
    const startTime = Date.now();
    
    try {
      const response = await fetch(`${apiUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000)
      });
      
      const responseTime = Date.now() - startTime;
      
      if (response.ok) {
        return {
          apiUrl,
          isReachable: true,
          responseTime
        };
      } else {
        return {
          apiUrl,
          isReachable: false,
          error: `HTTP ${response.status}: ${response.statusText}`
        };
      }
    } catch (error) {
      return {
        apiUrl,
        isReachable: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * Try to detect which port the backend is actually running on
   */
  private static async detectBackendPort(): Promise<number | null> {
    for (const port of this.COMMON_BACKEND_PORTS) {
      try {
        const response = await fetch(`http://localhost:${port}/health`, {
          method: 'GET',
          signal: AbortSignal.timeout(1000)
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.service && data.service.includes('EZBI')) {
            return port;
          }
        }
      } catch {
        // Port not available, continue
      }
    }
    return null;
  }

  /**
   * Get environment information for debugging
   */
  public static getEnvironmentInfo() {
    return {
      apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      nodeEnv: process.env.NODE_ENV || 'development',
      timestamp: new Date().toISOString(),
      userAgent: typeof window !== 'undefined' ? window.navigator.userAgent : 'Server-side'
    };
  }

  /**
   * Generate configuration suggestions
   */
  public static generateConfigSuggestions(validationResult: EnvValidationResult): string[] {
    const suggestions: string[] = [];
    
    if (!validationResult.isValid) {
      suggestions.push('🔧 Configuration Issues Detected:');
      
      validationResult.errors.forEach(error => {
        suggestions.push(`❌ ${error}`);
      });
      
      validationResult.warnings.forEach(warning => {
        suggestions.push(`⚠️ ${warning}`);
      });
      
      validationResult.suggestions.forEach(suggestion => {
        suggestions.push(`💡 ${suggestion}`);
      });
      
      if (validationResult.detectedBackendPort) {
        suggestions.push('');
        suggestions.push('🚀 Quick Fix:');
        suggestions.push(`1. Update your .env.local file:`);
        suggestions.push(`   NEXT_PUBLIC_API_URL=http://localhost:${validationResult.detectedBackendPort}`);
        suggestions.push(`2. Restart your frontend server`);
      }
    }
    
    return suggestions;
  }
}