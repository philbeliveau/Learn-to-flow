/**
 * Real-time Connection Monitoring System
 * Monitors backend connectivity and provides auto-retry mechanisms
 */

export interface ConnectionStatus {
  isConnected: boolean;
  lastChecked: Date;
  responseTime?: number;
  error?: string;
  consecutiveFailures: number;
  uptime: number; // percentage
}

export interface ConnectionMonitorConfig {
  checkInterval: number; // milliseconds
  timeout: number; // milliseconds
  maxRetries: number;
  backoffMultiplier: number;
  enableLogging: boolean;
}

export class ConnectionMonitor {
  private static instance: ConnectionMonitor;
  private config: ConnectionMonitorConfig;
  private status: ConnectionStatus;
  private intervalId: NodeJS.Timeout | null = null;
  private listeners: Set<(status: ConnectionStatus) => void> = new Set();
  private apiUrl: string;
  private totalChecks: number = 0;
  private successfulChecks: number = 0;

  private constructor(apiUrl: string, config: Partial<ConnectionMonitorConfig> = {}) {
    this.apiUrl = apiUrl;
    this.config = {
      checkInterval: 30000, // 30 seconds
      timeout: 5000, // 5 seconds
      maxRetries: 3,
      backoffMultiplier: 2,
      enableLogging: true,
      ...config
    };
    
    this.status = {
      isConnected: false,
      lastChecked: new Date(),
      consecutiveFailures: 0,
      uptime: 0
    };
  }

  public static getInstance(apiUrl?: string, config?: Partial<ConnectionMonitorConfig>): ConnectionMonitor {
    if (!ConnectionMonitor.instance) {
      if (!apiUrl) {
        throw new Error('API URL is required for first initialization');
      }
      ConnectionMonitor.instance = new ConnectionMonitor(apiUrl, config);
    }
    return ConnectionMonitor.instance;
  }

  /**
   * Get existing instance without requiring API URL (for cleanup)
   */
  public static getExistingInstance(): ConnectionMonitor | null {
    return ConnectionMonitor.instance;
  }

  /**
   * Destroy the singleton instance (for cleanup)
   */
  public static destroy(): void {
    if (ConnectionMonitor.instance) {
      ConnectionMonitor.instance.stopMonitoring();
      ConnectionMonitor.instance = undefined as any;
    }
  }

  /**
   * Start monitoring connection
   */
  public startMonitoring(): void {
    if (this.intervalId) {
      return; // Already monitoring
    }

    this.log('🔍 Starting connection monitoring...');
    
    // Initial check
    this.checkConnection();
    
    // Set up periodic checks
    this.intervalId = setInterval(() => {
      this.checkConnection();
    }, this.config.checkInterval);
  }

  /**
   * Stop monitoring connection
   */
  public stopMonitoring(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
      this.log('⏹️ Stopped connection monitoring');
    }
  }

  /**
   * Add a listener for connection status changes
   */
  public addListener(listener: (status: ConnectionStatus) => void): void {
    this.listeners.add(listener);
  }

  /**
   * Remove a listener
   */
  public removeListener(listener: (status: ConnectionStatus) => void): void {
    this.listeners.delete(listener);
  }

  /**
   * Get current connection status
   */
  public getStatus(): ConnectionStatus {
    return { ...this.status };
  }

  /**
   * Force a connection check
   */
  public async forceCheck(): Promise<ConnectionStatus> {
    await this.checkConnection();
    return this.getStatus();
  }

  /**
   * Check connection with retry logic
   */
  private async checkConnection(): Promise<void> {
    const startTime = Date.now();
    let attempts = 0;
    let lastError: string | undefined;

    while (attempts < this.config.maxRetries) {
      try {
        const response = await fetch(`${this.apiUrl}/health`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
          signal: AbortSignal.timeout(this.config.timeout)
        });

        if (response.ok) {
          const responseTime = Date.now() - startTime;
          this.handleSuccess(responseTime);
          return;
        } else {
          lastError = `HTTP ${response.status}: ${response.statusText}`;
        }
      } catch (error) {
        lastError = error instanceof Error ? error.message : 'Unknown error';
      }

      attempts++;
      
      // Exponential backoff for retries
      if (attempts < this.config.maxRetries) {
        const delay = Math.pow(this.config.backoffMultiplier, attempts) * 1000;
        this.log(`⏳ Retry ${attempts}/${this.config.maxRetries} in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    // All retries failed
    this.handleFailure(lastError);
  }

  /**
   * Handle successful connection
   */
  private handleSuccess(responseTime: number): void {
    this.totalChecks++;
    this.successfulChecks++;
    
    const wasDisconnected = !this.status.isConnected;
    
    this.status = {
      isConnected: true,
      lastChecked: new Date(),
      responseTime,
      error: undefined,
      consecutiveFailures: 0,
      uptime: (this.successfulChecks / this.totalChecks) * 100
    };

    if (wasDisconnected) {
      this.log('✅ Connection restored');
    } else {
      this.log(`🔄 Connection check passed (${responseTime}ms)`);
    }

    this.notifyListeners();
  }

  /**
   * Handle connection failure
   */
  private handleFailure(error?: string): void {
    this.totalChecks++;
    
    const wasConnected = this.status.isConnected;
    
    this.status = {
      isConnected: false,
      lastChecked: new Date(),
      error,
      consecutiveFailures: this.status.consecutiveFailures + 1,
      uptime: (this.successfulChecks / this.totalChecks) * 100
    };

    if (wasConnected) {
      this.log(`❌ Connection lost: ${error}`);
    } else {
      this.log(`🔄 Connection still down (${this.status.consecutiveFailures} failures)`);
    }

    this.notifyListeners();
  }

  /**
   * Notify all listeners of status change
   */
  private notifyListeners(): void {
    this.listeners.forEach(listener => {
      try {
        listener(this.getStatus());
      } catch (error) {
        console.error('Error in connection monitor listener:', error);
      }
    });
  }

  /**
   * Log messages if logging is enabled
   */
  private log(message: string): void {
    if (this.config.enableLogging) {
      console.log(`[ConnectionMonitor] ${message}`);
    }
  }

  /**
   * Get connection statistics
   */
  public getStats(): {
    totalChecks: number;
    successfulChecks: number;
    uptime: number;
    averageResponseTime?: number;
  } {
    return {
      totalChecks: this.totalChecks,
      successfulChecks: this.successfulChecks,
      uptime: this.status.uptime
    };
  }

  /**
   * Reset statistics
   */
  public resetStats(): void {
    this.totalChecks = 0;
    this.successfulChecks = 0;
    this.status.uptime = 0;
    this.status.consecutiveFailures = 0;
  }
}