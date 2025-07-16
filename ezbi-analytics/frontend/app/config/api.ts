/**
 * API Configuration
 * Centralized configuration for all API endpoints
 */

// Main API base URL - uses environment variable or defaults to local development
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Manufacturing API endpoints - all use the main API
export const MANUFACTURING_API_URL = API_BASE_URL;

// Auth API - uses the same server
export const AUTH_API_URL = API_BASE_URL;

// API endpoints
export const API_ENDPOINTS = {
  // Health check
  health: `${API_BASE_URL}/health`,
  
  // Authentication
  login: `${API_BASE_URL}/api/v1/login`,
  logout: `${API_BASE_URL}/api/v1/logout`,
  refresh: `${API_BASE_URL}/api/v1/refresh`,
  
  // Manufacturing endpoints
  manufacturing: {
    sales: `${API_BASE_URL}/api/manufacturing/sales`,
    operations: `${API_BASE_URL}/api/manufacturing/operations`,
    finance: `${API_BASE_URL}/api/manufacturing/finance`,
    hr: `${API_BASE_URL}/api/manufacturing/hr`,
    expenses: `${API_BASE_URL}/api/manufacturing/expenses`,
    accounting: `${API_BASE_URL}/api/manufacturing/accounting`,
  },
  
  // Dashboard endpoints
  dashboard: {
    kpis: `${API_BASE_URL}/api/v1/analytics/kpis`,
    predictions: `${API_BASE_URL}/api/v1/quick-prediction`,
    cashFlow: `${API_BASE_URL}/api/v1/current-cash-position`,
  }
};

export default API_BASE_URL;