/**
 * Synthetic Data Service
 * Ensures ALL dashboard data comes from our actual synthetic data sources
 * NO HARDCODED VALUES ALLOWED
 */

// API Base URLs for our synthetic data sources
const CASH_FLOW_API_BASE = 'http://localhost:8000'; // Our cash flow prediction API
const MANUFACTURING_API_BASE = 'http://localhost:8004'; // Existing EZBI API

export interface SyntheticDataConfig {
  useCashFlowAPI: boolean;
  useManufacturingAPI: boolean;
  usePostgreSQLDirect: boolean;
  useExcelData: boolean;
}

export class SyntheticDataService {
  private config: SyntheticDataConfig;
  
  constructor(config: SyntheticDataConfig = {
    useCashFlowAPI: true,
    useManufacturingAPI: true,
    usePostgreSQLDirect: true,
    useExcelData: true
  }) {
    this.config = config;
  }

  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Get real current cash position from PostgreSQL
   * NO HARDCODED VALUES
   */
  async getCurrentCashPosition(): Promise<any> {
    if (!this.config.useCashFlowAPI) {
      throw new Error('Cash Flow API disabled');
    }

    try {
      const response = await fetch(
        `${CASH_FLOW_API_BASE}/api/v1/current-cash-position`,
        { headers: this.getAuthHeaders() }
      );
      
      if (!response.ok) {
        throw new Error(`Cash position API error: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Validate that we got real data from PostgreSQL
      if (!data.success || !data.current_position) {
        throw new Error('Invalid cash position data structure');
      }
      
      return data;
    } catch (error) {
      console.error('Failed to get real cash position:', error);
      throw error;
    }
  }

  /**
   * Get real cash flow predictions from our ML engine
   * Uses actual PostgreSQL + Excel data
   */
  async getCashFlowPrediction(days: number = 30): Promise<any> {
    if (!this.config.useCashFlowAPI) {
      throw new Error('Cash Flow API disabled');
    }

    try {
      const response = await fetch(
        `${CASH_FLOW_API_BASE}/api/v1/quick-prediction?days=${days}`,
        { headers: this.getAuthHeaders() }
      );
      
      if (!response.ok) {
        throw new Error(`Prediction API error: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Validate that predictions come from real data
      if (!data.success || !data.summary) {
        throw new Error('Invalid prediction data structure');
      }
      
      return data;
    } catch (error) {
      console.error('Failed to get real predictions:', error);
      throw error;
    }
  }

  /**
   * Get comprehensive cash flow dashboard data
   * Uses both PostgreSQL operational data and Excel business planning
   */
  async getComprehensiveCashFlowData(): Promise<any> {
    if (!this.config.useCashFlowAPI) {
      throw new Error('Cash Flow API disabled');
    }

    try {
      const response = await fetch(
        `${CASH_FLOW_API_BASE}/api/v1/cash-flow-dashboard`,
        { headers: this.getAuthHeaders() }
      );
      
      if (!response.ok) {
        throw new Error(`Dashboard API error: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Validate comprehensive data structure
      if (!data.success || !data.current_position || !data.predictions) {
        throw new Error('Invalid dashboard data structure');
      }
      
      return data;
    } catch (error) {
      console.error('Failed to get comprehensive dashboard data:', error);
      throw error;
    }
  }

  /**
   * Generate full cash flow prediction with scenarios
   * Uses our ML ensemble model with PostgreSQL + Excel integration
   */
  async generateFullPrediction(startDate: string, endDate: string): Promise<any> {
    if (!this.config.useCashFlowAPI) {
      throw new Error('Cash Flow API disabled');
    }

    try {
      const response = await fetch(
        `${CASH_FLOW_API_BASE}/api/v1/predict-cash-flow`,
        {
          method: 'POST',
          headers: this.getAuthHeaders(),
          body: JSON.stringify({
            start_date: startDate,
            end_date: endDate,
            model_type: 'ensemble',
            include_scenarios: true
          })
        }
      );
      
      if (!response.ok) {
        throw new Error(`Full prediction API error: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Validate full prediction data
      if (!data.success || !data.predictions || !data.scenarios || !data.insights) {
        throw new Error('Invalid full prediction data structure');
      }
      
      return data;
    } catch (error) {
      console.error('Failed to generate full prediction:', error);
      throw error;
    }
  }

  /**
   * Get real financial data from manufacturing database
   * NO HARDCODED VALUES
   */
  async getFinancialData(timeframe: string = '6M'): Promise<any> {
    if (!this.config.useManufacturingAPI) {
      throw new Error('Manufacturing API disabled');
    }

    try {
      const response = await fetch(
        `${MANUFACTURING_API_BASE}/api/v1/analytics/cash-flow-timeline?timeframe=${timeframe}`,
        { headers: this.getAuthHeaders() }
      );
      
      if (!response.ok) {
        throw new Error(`Financial data API error: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Validate that we got real financial data
      if (!data.chart_data) {
        throw new Error('Invalid financial data structure');
      }
      
      return data;
    } catch (error) {
      console.error('Failed to get real financial data:', error);
      throw error;
    }
  }

  /**
   * Get real banking trends from manufacturing database
   */
  async getBankingTrends(): Promise<any> {
    if (!this.config.useManufacturingAPI) {
      throw new Error('Manufacturing API disabled');
    }

    try {
      const response = await fetch(
        `${MANUFACTURING_API_BASE}/api/v1/analytics/banking-trends`,
        { headers: this.getAuthHeaders() }
      );
      
      if (!response.ok) {
        throw new Error(`Banking trends API error: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Validate banking trends data
      if (!data.charts) {
        throw new Error('Invalid banking trends data structure');
      }
      
      return data;
    } catch (error) {
      console.error('Failed to get real banking trends:', error);
      throw error;
    }
  }

  /**
   * Get real KPIs from manufacturing database
   */
  async getKPIs(): Promise<any> {
    if (!this.config.useManufacturingAPI) {
      throw new Error('Manufacturing API disabled');
    }

    try {
      const response = await fetch(
        `${MANUFACTURING_API_BASE}/api/v1/company/kpis`,
        { headers: this.getAuthHeaders() }
      );
      
      if (!response.ok) {
        throw new Error(`KPIs API error: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Validate KPI data structure
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid KPI data structure');
      }
      
      return data;
    } catch (error) {
      console.error('Failed to get real KPIs:', error);
      throw error;
    }
  }

  /**
   * Get real manufacturing dashboard data
   */
  async getManufacturingData(): Promise<any> {
    if (!this.config.useManufacturingAPI) {
      throw new Error('Manufacturing API disabled');
    }

    try {
      const response = await fetch(
        `${MANUFACTURING_API_BASE}/api/v1/analytics/manufacturing-dashboard`,
        { headers: this.getAuthHeaders() }
      );
      
      if (!response.ok) {
        throw new Error(`Manufacturing data API error: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Validate manufacturing data
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid manufacturing data structure');
      }
      
      return data;
    } catch (error) {
      console.error('Failed to get real manufacturing data:', error);
      throw error;
    }
  }

  /**
   * Get business planning file status
   * Shows status of our Excel business planning files
   */
  async getBusinessPlanningStatus(): Promise<any> {
    if (!this.config.useCashFlowAPI) {
      throw new Error('Cash Flow API disabled');
    }

    try {
      const response = await fetch(
        `${CASH_FLOW_API_BASE}/api/v1/business-planning-status`,
        { headers: this.getAuthHeaders() }
      );
      
      if (!response.ok) {
        throw new Error(`Business planning status API error: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Validate business planning status
      if (!data.success || !data.files) {
        throw new Error('Invalid business planning status data');
      }
      
      return data;
    } catch (error) {
      console.error('Failed to get business planning status:', error);
      throw error;
    }
  }

  /**
   * Regenerate business planning Excel files
   */
  async regenerateBusinessPlanning(): Promise<any> {
    if (!this.config.useCashFlowAPI) {
      throw new Error('Cash Flow API disabled');
    }

    try {
      const response = await fetch(
        `${CASH_FLOW_API_BASE}/api/v1/regenerate-business-planning`,
        { 
          method: 'POST',
          headers: this.getAuthHeaders()
        }
      );
      
      if (!response.ok) {
        throw new Error(`Business planning regeneration API error: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Validate regeneration response
      if (!data.success) {
        throw new Error('Business planning regeneration failed');
      }
      
      return data;
    } catch (error) {
      console.error('Failed to regenerate business planning:', error);
      throw error;
    }
  }

  /**
   * Get model performance metrics
   * Shows actual performance of our ML models
   */
  async getModelPerformance(): Promise<any> {
    if (!this.config.useCashFlowAPI) {
      throw new Error('Cash Flow API disabled');
    }

    try {
      const response = await fetch(
        `${CASH_FLOW_API_BASE}/api/v1/model-performance`,
        { headers: this.getAuthHeaders() }
      );
      
      if (!response.ok) {
        throw new Error(`Model performance API error: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Validate model performance data
      if (!data.success || !data.model_info) {
        throw new Error('Invalid model performance data');
      }
      
      return data;
    } catch (error) {
      console.error('Failed to get model performance:', error);
      throw error;
    }
  }

  /**
   * Validate that all data sources are available and returning real data
   */
  async validateDataSources(): Promise<{
    cashFlowAPI: boolean;
    manufacturingAPI: boolean;
    postgresqlData: boolean;
    excelData: boolean;
    overallHealth: boolean;
  }> {
    const results = {
      cashFlowAPI: false,
      manufacturingAPI: false,
      postgresqlData: false,
      excelData: false,
      overallHealth: false
    };

    try {
      // Test cash flow API
      if (this.config.useCashFlowAPI) {
        const cashPosition = await this.getCurrentCashPosition();
        results.cashFlowAPI = !!cashPosition.success;
        results.postgresqlData = !!cashPosition.current_position;
      }

      // Test manufacturing API
      if (this.config.useManufacturingAPI) {
        const kpis = await this.getKPIs();
        results.manufacturingAPI = !!kpis;
      }

      // Test Excel data availability
      if (this.config.useExcelData && this.config.useCashFlowAPI) {
        const planningStatus = await this.getBusinessPlanningStatus();
        results.excelData = planningStatus.total_files > 0;
      }

      results.overallHealth = results.cashFlowAPI && results.manufacturingAPI && 
                            results.postgresqlData && results.excelData;

    } catch (error) {
      console.error('Data source validation failed:', error);
    }

    return results;
  }
}

// Create singleton instance
export const syntheticDataService = new SyntheticDataService();

// Export utility functions
export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('fr-FR', { 
    style: 'currency', 
    currency: 'EUR',
    minimumFractionDigits: 0
  }).format(amount);
};

export const formatPercentage = (value: number): string => {
  return `${value.toFixed(1)}%`;
};

export const formatDate = (date: string | Date): string => {
  const d = new Date(date);
  return d.toLocaleDateString('fr-FR', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  });
};

// Export validation function for components
export const validateRealData = (data: any, requiredFields: string[]): boolean => {
  if (!data || typeof data !== 'object') {
    console.error('Data validation failed: No data object');
    return false;
  }

  for (const field of requiredFields) {
    if (!(field in data)) {
      console.error(`Data validation failed: Missing field ${field}`);
      return false;
    }
  }

  return true;
};