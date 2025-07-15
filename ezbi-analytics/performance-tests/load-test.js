// Load Testing Configuration for EZBI Analytics Platform
// DevOps Engineer Implementation - SPARC Production Deployment

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Counter, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const apiCalls = new Counter('api_calls');
const responseTime = new Trend('response_time');

// Test configuration
export let options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up to 10 users over 2 minutes
    { duration: '5m', target: 10 },   // Stay at 10 users for 5 minutes
    { duration: '2m', target: 20 },   // Ramp up to 20 users over 2 minutes
    { duration: '5m', target: 20 },   // Stay at 20 users for 5 minutes
    { duration: '2m', target: 50 },   // Ramp up to 50 users over 2 minutes
    { duration: '5m', target: 50 },   // Stay at 50 users for 5 minutes
    { duration: '2m', target: 100 },  // Ramp up to 100 users over 2 minutes
    { duration: '5m', target: 100 },  // Stay at 100 users for 5 minutes
    { duration: '2m', target: 0 },    // Ramp down to 0 users over 2 minutes
  ],
  thresholds: {
    'http_req_duration': ['p(95)<2000'],     // 95% of requests should be below 2s
    'http_req_failed': ['rate<0.05'],        // Error rate should be below 5%
    'error_rate': ['rate<0.05'],             // Custom error rate should be below 5%
    'response_time': ['p(95)<2000'],         // 95% of response times should be below 2s
  },
};

// Base URL configuration
const BASE_URL = __ENV.BASE_URL || 'https://api.ezbi.fr';
const ML_URL = __ENV.ML_URL || 'https://ml.ezbi.fr';

// Test user credentials
const TEST_USER = {
  email: 'test@example.com',
  password: 'TestPassword123!'
};

// Authentication token storage
let authToken = null;

// Helper function to authenticate
function authenticate() {
  const loginPayload = JSON.stringify(TEST_USER);
  const loginParams = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  const loginResponse = http.post(`${BASE_URL}/api/v1/auth/login`, loginPayload, loginParams);
  
  if (loginResponse.status === 200) {
    const responseBody = JSON.parse(loginResponse.body);
    authToken = responseBody.access_token;
    return true;
  }
  
  return false;
}

// Helper function to get authenticated headers
function getAuthHeaders() {
  return {
    'Authorization': `Bearer ${authToken}`,
    'Content-Type': 'application/json',
  };
}

// Main test function
export default function() {
  // Authenticate if needed
  if (!authToken) {
    if (!authenticate()) {
      console.log('Authentication failed');
      return;
    }
  }
  
  // Test scenarios
  const scenarios = [
    testHealthEndpoints,
    testAuthenticationFlow,
    testDataEndpoints,
    testMLPredictions,
    testFileUpload,
    testDashboardData,
  ];
  
  // Run a random scenario
  const scenario = scenarios[Math.floor(Math.random() * scenarios.length)];
  scenario();
  
  // Sleep between requests
  sleep(1);
}

// Test health endpoints
function testHealthEndpoints() {
  const endpoints = [
    `${BASE_URL}/health`,
    `${ML_URL}/health`,
  ];
  
  endpoints.forEach(endpoint => {
    const response = http.get(endpoint);
    
    check(response, {
      'health check status is 200': (r) => r.status === 200,
      'health check response time < 1000ms': (r) => r.timings.duration < 1000,
    });
    
    errorRate.add(response.status !== 200);
    apiCalls.add(1);
    responseTime.add(response.timings.duration);
  });
}

// Test authentication flow
function testAuthenticationFlow() {
  // Login
  const loginPayload = JSON.stringify(TEST_USER);
  const loginParams = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  const loginResponse = http.post(`${BASE_URL}/api/v1/auth/login`, loginPayload, loginParams);
  
  check(loginResponse, {
    'login status is 200': (r) => r.status === 200,
    'login response time < 2000ms': (r) => r.timings.duration < 2000,
    'login returns access token': (r) => {
      const body = JSON.parse(r.body);
      return body.access_token !== undefined;
    },
  });
  
  if (loginResponse.status === 200) {
    const responseBody = JSON.parse(loginResponse.body);
    const token = responseBody.access_token;
    
    // Test protected endpoint
    const protectedResponse = http.get(`${BASE_URL}/api/v1/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    check(protectedResponse, {
      'protected endpoint status is 200': (r) => r.status === 200,
      'protected endpoint response time < 1000ms': (r) => r.timings.duration < 1000,
    });
    
    errorRate.add(protectedResponse.status !== 200);
    apiCalls.add(1);
    responseTime.add(protectedResponse.timings.duration);
  }
  
  errorRate.add(loginResponse.status !== 200);
  apiCalls.add(1);
  responseTime.add(loginResponse.timings.duration);
}

// Test data endpoints
function testDataEndpoints() {
  const endpoints = [
    `${BASE_URL}/api/v1/data/financial`,
    `${BASE_URL}/api/v1/data/manufacturing`,
    `${BASE_URL}/api/v1/data/analytics`,
  ];
  
  endpoints.forEach(endpoint => {
    const response = http.get(endpoint, {
      headers: getAuthHeaders(),
    });
    
    check(response, {
      'data endpoint status is 200': (r) => r.status === 200,
      'data endpoint response time < 3000ms': (r) => r.timings.duration < 3000,
      'data endpoint returns JSON': (r) => {
        try {
          JSON.parse(r.body);
          return true;
        } catch (e) {
          return false;
        }
      },
    });
    
    errorRate.add(response.status !== 200);
    apiCalls.add(1);
    responseTime.add(response.timings.duration);
  });
}

// Test ML predictions
function testMLPredictions() {
  const predictionPayload = JSON.stringify({
    features: [
      { name: 'revenue', value: 1000000 },
      { name: 'expenses', value: 800000 },
      { name: 'growth_rate', value: 0.15 },
    ],
    model_type: 'cash_flow_prediction',
    prediction_horizon: 12,
  });
  
  const response = http.post(`${ML_URL}/api/v1/predict`, predictionPayload, {
    headers: getAuthHeaders(),
  });
  
  check(response, {
    'ML prediction status is 200': (r) => r.status === 200,
    'ML prediction response time < 5000ms': (r) => r.timings.duration < 5000,
    'ML prediction returns results': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.predictions !== undefined;
      } catch (e) {
        return false;
      }
    },
  });
  
  errorRate.add(response.status !== 200);
  apiCalls.add(1);
  responseTime.add(response.timings.duration);
}

// Test file upload
function testFileUpload() {
  const fileData = 'company,revenue,expenses\nCompany A,1000000,800000\nCompany B,2000000,1600000';
  
  const response = http.post(`${BASE_URL}/api/v1/upload/csv`, {
    file: http.file(fileData, 'test_data.csv', 'text/csv'),
  }, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
    },
  });
  
  check(response, {
    'file upload status is 200': (r) => r.status === 200,
    'file upload response time < 10000ms': (r) => r.timings.duration < 10000,
  });
  
  errorRate.add(response.status !== 200);
  apiCalls.add(1);
  responseTime.add(response.timings.duration);
}

// Test dashboard data
function testDashboardData() {
  const dashboardEndpoints = [
    `${BASE_URL}/api/v1/dashboard/overview`,
    `${BASE_URL}/api/v1/dashboard/financial-metrics`,
    `${BASE_URL}/api/v1/dashboard/manufacturing-metrics`,
    `${BASE_URL}/api/v1/dashboard/predictions`,
  ];
  
  dashboardEndpoints.forEach(endpoint => {
    const response = http.get(endpoint, {
      headers: getAuthHeaders(),
    });
    
    check(response, {
      'dashboard endpoint status is 200': (r) => r.status === 200,
      'dashboard endpoint response time < 2000ms': (r) => r.timings.duration < 2000,
    });
    
    errorRate.add(response.status !== 200);
    apiCalls.add(1);
    responseTime.add(response.timings.duration);
  });
}

// Setup function (runs once per VU)
export function setup() {
  console.log('Setting up load test...');
  
  // Create test user if needed
  const registerPayload = JSON.stringify({
    email: TEST_USER.email,
    password: TEST_USER.password,
    full_name: 'Test User',
    company: 'Test Company',
  });
  
  const registerResponse = http.post(`${BASE_URL}/api/v1/auth/register`, registerPayload, {
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  console.log(`Test user registration status: ${registerResponse.status}`);
  
  return {
    baseUrl: BASE_URL,
    mlUrl: ML_URL,
  };
}

// Teardown function (runs once after all VUs)
export function teardown(data) {
  console.log('Tearing down load test...');
  console.log(`Base URL: ${data.baseUrl}`);
  console.log(`ML URL: ${data.mlUrl}`);
}