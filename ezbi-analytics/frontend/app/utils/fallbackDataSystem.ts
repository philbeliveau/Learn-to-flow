/**
 * 🛡️ Fallback Data System
 * Provides backup data when APIs are unavailable
 */

export interface FallbackData {
  [key: string]: any;
}

export interface FallbackConfig {
  useLocalStorage: boolean;
  localStorageKey: string;
  maxAge: number; // milliseconds
  generateFallback: () => any;
}

export class FallbackDataSystem {
  private static instance: FallbackDataSystem;
  private fallbackConfigs: Map<string, FallbackConfig> = new Map();
  private cachedData: Map<string, { data: any; timestamp: number }> = new Map();

  private constructor() {}

  static getInstance(): FallbackDataSystem {
    if (!FallbackDataSystem.instance) {
      FallbackDataSystem.instance = new FallbackDataSystem();
    }
    return FallbackDataSystem.instance;
  }

  /**
   * Register fallback configuration for an endpoint
   */
  registerFallback(endpoint: string, config: FallbackConfig): void {
    this.fallbackConfigs.set(endpoint, config);
  }

  /**
   * Get fallback data for an endpoint
   */
  getFallbackData(endpoint: string): any {
    const config = this.fallbackConfigs.get(endpoint);
    
    if (!config) {
      return this.getDefaultFallback(endpoint);
    }

    // Check cached data first
    const cached = this.cachedData.get(endpoint);
    if (cached && (Date.now() - cached.timestamp) < config.maxAge) {
      return cached.data;
    }

    // Try local storage
    if (config.useLocalStorage && typeof window !== 'undefined') {
      const stored = localStorage.getItem(config.localStorageKey);
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          if (parsed.timestamp && (Date.now() - parsed.timestamp) < config.maxAge) {
            this.cachedData.set(endpoint, { data: parsed.data, timestamp: parsed.timestamp });
            return parsed.data;
          }
        } catch (error) {
          console.warn('Failed to parse fallback data from localStorage:', error);
        }
      }
    }

    // Generate new fallback data
    const fallbackData = config.generateFallback();
    const timestamp = Date.now();
    
    // Cache in memory
    this.cachedData.set(endpoint, { data: fallbackData, timestamp });
    
    // Store in localStorage
    if (config.useLocalStorage && typeof window !== 'undefined') {
      try {
        localStorage.setItem(config.localStorageKey, JSON.stringify({
          data: fallbackData,
          timestamp
        }));
      } catch (error) {
        console.warn('Failed to store fallback data in localStorage:', error);
      }
    }

    return fallbackData;
  }

  /**
   * Store successful response data for future fallback
   */
  storeSuccessfulResponse(endpoint: string, data: any): void {
    const config = this.fallbackConfigs.get(endpoint);
    if (!config) return;

    const timestamp = Date.now();
    
    // Cache in memory
    this.cachedData.set(endpoint, { data, timestamp });
    
    // Store in localStorage
    if (config.useLocalStorage && typeof window !== 'undefined') {
      try {
        localStorage.setItem(config.localStorageKey, JSON.stringify({
          data,
          timestamp
        }));
      } catch (error) {
        console.warn('Failed to store successful response in localStorage:', error);
      }
    }
  }

  /**
   * Get default fallback data based on endpoint pattern
   */
  private getDefaultFallback(endpoint: string): any {
    if (endpoint.includes('kpis')) {
      return this.getDefaultKPIFallback();
    } else if (endpoint.includes('dashboard')) {
      return this.getDefaultDashboardFallback();
    } else if (endpoint.includes('products')) {
      return this.getDefaultProductsFallback();
    } else if (endpoint.includes('finance')) {
      return this.getDefaultFinanceFallback();
    } else if (endpoint.includes('sales')) {
      return this.getDefaultSalesFallback();
    }
    
    return { 
      success: false, 
      message: 'No fallback data available',
      fallback: true 
    };
  }

  private getDefaultKPIFallback(): any {
    return {
      success: true,
      fallback: true,
      message: 'Using fallback data - API temporarily unavailable',
      total_customers: 45,
      total_revenue: 285000.00,
      total_orders: 128,
      active_employees: 30,
      efficiency: 0.82,
      timestamp: new Date().toISOString()
    };
  }

  private getDefaultDashboardFallback(): any {
    return {
      success: true,
      fallback: true,
      message: 'Using fallback data - API temporarily unavailable',
      overview: {
        total_customers: 45,
        total_revenue: 285000.00,
        total_orders: 128,
        total_units_produced: 95,
        active_employees: 30,
        monthly_fixed_costs: 85000.00,
        total_debt: 125000.00,
        total_receivables: 57000.00
      },
      recent_activity: [
        {
          type: 'Invoice',
          reference: 'INV-FALLBACK-001',
          amount: 12500.00,
          date: new Date().toISOString(),
          customer: 'Manufacturing Corp (Cached)'
        }
      ],
      timestamp: new Date().toISOString()
    };
  }

  private getDefaultProductsFallback(): any {
    return {
      success: true,
      fallback: true,
      message: 'Using fallback data - API temporarily unavailable',
      total_products: 18,
      total_production_orders: 42,
      production_efficiency: 0.82,
      capacity_utilization: 0.75,
      active_orders: 12,
      recent_production: [
        {
          product: 'Engine Component (Cached)',
          quantity: 120,
          status: 'completed'
        }
      ],
      timestamp: new Date().toISOString()
    };
  }

  private getDefaultFinanceFallback(): any {
    return {
      success: true,
      fallback: true,
      message: 'Using fallback data - API temporarily unavailable',
      cash_balance: 245000.00,
      accounts_receivable: 57000.00,
      accounts_payable: 32000.00,
      debt_accounts: 125000.00,
      working_capital: 270000.00,
      monthly_burn_rate: 85000.00,
      days_cash_remaining: 86,
      timestamp: new Date().toISOString()
    };
  }

  private getDefaultSalesFallback(): any {
    return {
      success: true,
      fallback: true,
      message: 'Using fallback data - API temporarily unavailable',
      total_customers: 45,
      total_invoices: 128,
      revenue_this_month: 285000.00,
      revenue_last_month: 267000.00,
      avg_order_value: 2226.56,
      top_customers: [
        { name: 'Manufacturing Corp (Cached)', revenue: 35000.00 },
        { name: 'Steel Works Ltd (Cached)', revenue: 28000.00 }
      ],
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Clear all cached fallback data
   */
  clearCache(): void {
    this.cachedData.clear();
    
    if (typeof window !== 'undefined') {
      this.fallbackConfigs.forEach(config => {
        if (config.useLocalStorage) {
          localStorage.removeItem(config.localStorageKey);
        }
      });
    }
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): Record<string, any> {
    const stats: Record<string, any> = {};
    
    this.cachedData.forEach((cache, endpoint) => {
      stats[endpoint] = {
        hasData: !!cache.data,
        timestamp: cache.timestamp,
        age: Date.now() - cache.timestamp,
        size: JSON.stringify(cache.data).length
      };
    });
    
    return stats;
  }
}

// Export singleton instance
export const fallbackDataSystem = FallbackDataSystem.getInstance();

// Setup default fallback configurations
export const setupDefaultFallbacks = () => {
  const system = FallbackDataSystem.getInstance();
  
  // Sales KPIs fallback
  system.registerFallback('/api/manufacturing/sales/kpis', {
    useLocalStorage: true,
    localStorageKey: 'ezbi_fallback_sales_kpis',
    maxAge: 30 * 60 * 1000, // 30 minutes
    generateFallback: () => ({
      success: true,
      fallback: true,
      message: 'Using fallback data - Sales API temporarily unavailable',
      total_customers: 45,
      total_invoices: 128,
      revenue_this_month: 285000.00,
      revenue_last_month: 267000.00,
      avg_order_value: 2226.56,
      top_customers: [
        { name: 'Manufacturing Corp (Cached)', revenue: 35000.00 },
        { name: 'Steel Works Ltd (Cached)', revenue: 28000.00 }
      ],
      timestamp: new Date().toISOString()
    })
  });

  // Operations fallback
  system.registerFallback('/api/manufacturing/operations/products', {
    useLocalStorage: true,
    localStorageKey: 'ezbi_fallback_operations_products',
    maxAge: 30 * 60 * 1000, // 30 minutes
    generateFallback: () => ({
      success: true,
      fallback: true,
      message: 'Using fallback data - Operations API temporarily unavailable',
      total_products: 18,
      total_production_orders: 42,
      production_efficiency: 0.82,
      capacity_utilization: 0.75,
      active_orders: 12,
      recent_production: [
        {
          product: 'Engine Component (Cached)',
          quantity: 120,
          status: 'completed'
        }
      ],
      timestamp: new Date().toISOString()
    })
  });

  // Finance fallback
  system.registerFallback('/api/manufacturing/finance/summary', {
    useLocalStorage: true,
    localStorageKey: 'ezbi_fallback_finance_summary',
    maxAge: 30 * 60 * 1000, // 30 minutes
    generateFallback: () => ({
      success: true,
      fallback: true,
      message: 'Using fallback data - Finance API temporarily unavailable',
      cash_balance: 245000.00,
      accounts_receivable: 57000.00,
      accounts_payable: 32000.00,
      debt_accounts: 125000.00,
      working_capital: 270000.00,
      monthly_burn_rate: 85000.00,
      days_cash_remaining: 86,
      timestamp: new Date().toISOString()
    })
  });

  // Dashboard fallback
  system.registerFallback('/api/v1/analytics/manufacturing-dashboard', {
    useLocalStorage: true,
    localStorageKey: 'ezbi_fallback_dashboard',
    maxAge: 15 * 60 * 1000, // 15 minutes
    generateFallback: () => ({
      success: true,
      fallback: true,
      message: 'Using fallback data - Dashboard API temporarily unavailable',
      overview: {
        total_customers: 45,
        total_revenue: 285000.00,
        total_orders: 128,
        total_units_produced: 95,
        active_employees: 30,
        monthly_fixed_costs: 85000.00,
        total_debt: 125000.00,
        total_receivables: 57000.00
      },
      recent_activity: [
        {
          type: 'Invoice',
          reference: 'INV-FALLBACK-001',
          amount: 12500.00,
          date: new Date().toISOString(),
          customer: 'Manufacturing Corp (Cached)'
        }
      ],
      timestamp: new Date().toISOString()
    })
  });

  console.log('✅ Default fallback configurations registered');
};