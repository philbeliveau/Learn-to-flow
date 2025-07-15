# Cash Flow Prediction Engine

## 🎯 Overview

This cash flow prediction engine combines **operational data from PostgreSQL** with **business planning data from Excel** to provide accurate, data-driven cash flow forecasts for manufacturing companies.

## 🏗️ Architecture

### **Data Sources Integration**:
```
PostgreSQL Database (Operational Data)
├── Historical cash flows
├── Customer payment patterns  
├── Accounts receivable aging
├── Payroll patterns
└── Vendor payment history

Excel Business Planning (Forward-Looking Data)
├── Supplier contracts & payment schedules
├── Customer forecasts & sales pipeline
├── Operating budget & expense planning
├── Capital expenditure plans
└── Inventory & procurement schedules

Combined Prediction Engine
├── Machine learning models (Linear Regression, Random Forest)
├── Scenario analysis (Base, Optimistic, Pessimistic, Stress Test)
├── Confidence intervals & uncertainty quantification
└── Actionable insights & recommendations
```

## 🔧 Components

### **1. Core Engine** (`cash_flow_prediction_engine.py`)
- **Data Integration**: Combines PostgreSQL operational data with Excel business planning
- **ML Models**: Ensemble of Linear Regression and Random Forest
- **Scenario Analysis**: Multiple scenarios with confidence intervals
- **Intelligent Insights**: Risk factors, opportunities, and recommendations

### **2. API Service** (`cash_flow_api.py`)
- **FastAPI RESTful API** for cash flow predictions
- **Real-time endpoints** for current cash position
- **Dashboard data** generation for EZBI platform
- **Background tasks** for Excel file regeneration

### **3. Excel Generator** (`realistic_excel_generator.py`)
- **Realistic business planning files** with authentic data
- **4 main Excel files**: supplier contracts, customer forecasts, budget planning, inventory planning
- **Multiple worksheets** per file with supporting analysis
- **Metadata generation** for automation

## 📊 Prediction Components

### **Cash Inflows** (Predicted from):
- **Customer payments** (PostgreSQL AR aging + payment patterns)
- **New orders** (Excel customer forecasts)
- **Seasonal adjustments** (Excel forecast models)

### **Cash Outflows** (Predicted from):
- **Supplier payments** (Excel supplier contracts + payment schedules)
- **Payroll** (PostgreSQL payroll patterns)
- **Operating expenses** (Excel budget planning)
- **Capital expenditure** (Excel capex planning)
- **Inventory purchases** (Excel procurement schedules)

## 🚀 API Endpoints

### **1. Generate Cash Flow Prediction**
```bash
POST /api/v1/predict-cash-flow
```
**Request**:
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-03-31",
  "model_type": "ensemble",
  "include_scenarios": true
}
```

**Response**:
```json
{
  "success": true,
  "prediction_info": {
    "start_date": "2024-01-01",
    "end_date": "2024-03-31",
    "model_type": "ensemble",
    "data_sources": ["postgresql_operational", "excel_business_planning"]
  },
  "predictions": {
    "daily_predictions": [...],
    "weekly_summary": [...],
    "monthly_summary": [...]
  },
  "scenarios": {
    "base_case": {...},
    "optimistic": {...},
    "pessimistic": {...},
    "stress_test": {...}
  },
  "insights": {
    "key_insights": [...],
    "risk_factors": [...],
    "opportunities": [...],
    "recommendations": [...]
  }
}
```

### **2. Quick Prediction**
```bash
GET /api/v1/quick-prediction?days=30
```
**Response**:
```json
{
  "success": true,
  "period": "30 days",
  "summary": {
    "total_predicted_inflows": 1500000.00,
    "total_predicted_outflows": 1200000.00,
    "net_cash_flow": 300000.00,
    "ending_balance": 450000.00
  },
  "risk_factors": [...],
  "key_insights": [...]
}
```

### **3. Current Cash Position**
```bash
GET /api/v1/current-cash-position
```
**Response**:
```json
{
  "success": true,
  "current_position": {
    "cash_balance": 150000.00,
    "outstanding_receivables": 89000.00,
    "outstanding_payables": 45000.00,
    "net_working_capital": 194000.00
  },
  "today_activity": {
    "inflows": 25000.00,
    "outflows": 18000.00,
    "net_flow": 7000.00,
    "transaction_count": 12
  }
}
```

### **4. Cash Flow Dashboard**
```bash
GET /api/v1/cash-flow-dashboard
```
**Response**: Complete dashboard data with charts, scenarios, and insights

## 🎨 Dashboard Integration

### **Chart Configurations**:

#### **1. Cash Flow Forecast Chart**
```javascript
{
  type: 'line',
  title: 'Cash Flow Forecast',
  data: {
    labels: ['2024-01-01', '2024-01-02', '2024-01-03', ...],
    datasets: [
      {
        label: 'Predicted Inflows',
        data: [125000, 89000, 156000, ...],
        borderColor: '#10B981'
      },
      {
        label: 'Predicted Outflows', 
        data: [98000, 67000, 123000, ...],
        borderColor: '#EF4444'
      },
      {
        label: 'Net Cash Flow',
        data: [27000, 22000, 33000, ...],
        borderColor: '#3B82F6'
      }
    ]
  }
}
```

#### **2. Cumulative Cash Balance Chart**
```javascript
{
  type: 'line',
  title: 'Cumulative Cash Balance',
  data: {
    labels: ['2024-01-01', '2024-01-02', '2024-01-03', ...],
    datasets: [{
      label: 'Cumulative Balance',
      data: [150000, 172000, 205000, ...],
      borderColor: '#8B5CF6',
      fill: true
    }]
  }
}
```

#### **3. Scenario Comparison Chart**
```javascript
{
  type: 'bar',
  title: 'Scenario Comparison',
  data: {
    labels: ['Base Case', 'Optimistic', 'Pessimistic'],
    datasets: [{
      label: 'Month-End Balance',
      data: [450000, 580000, 320000],
      backgroundColor: ['#3B82F6', '#10B981', '#EF4444']
    }]
  }
}
```

## 🎯 Business Value

### **1. Accurate Predictions**
- **Combines operational history** with forward-looking business plans
- **Machine learning models** trained on actual payment patterns
- **Confidence intervals** for uncertainty quantification

### **2. Actionable Insights**
- **Risk factors** identification (negative cash flow, large outflows)
- **Opportunities** for cash optimization
- **Specific recommendations** for cash flow management

### **3. Scenario Planning**
- **Multiple scenarios** (Base, Optimistic, Pessimistic, Stress Test)
- **What-if analysis** for different market conditions
- **Sensitivity analysis** for key assumptions

### **4. Real-time Monitoring**
- **Current cash position** tracking
- **Daily activity** monitoring
- **Automated alerts** for cash flow issues

## 🔧 Configuration

### **Environment Variables**:
```bash
# Database Configuration
DATABASE_URL=postgresql://user:pass@host:port/manufacturing_db

# Excel Data Path
EXCEL_DATA_PATH=/app/business-planning

# Prediction Configuration
PREDICTION_HORIZON_DAYS=90
CONFIDENCE_INTERVAL=0.95
MODEL_TYPE=ensemble
RETRAIN_FREQUENCY_DAYS=7
```

### **Model Configuration**:
```python
config = CashFlowPredictionConfig(
    database_url=DATABASE_URL,
    excel_data_path="/app/business-planning",
    prediction_horizon_days=90,
    confidence_interval=0.95,
    model_type="ensemble",  # 'linear', 'random_forest', 'ensemble'
    retrain_frequency_days=7
)
```

## 📈 Example Usage

### **1. Initialize Engine**
```python
from cash_flow_prediction_engine import create_cash_flow_prediction_engine

engine = create_cash_flow_prediction_engine(DATABASE_URL)
await engine.initialize_connection_pool()
```

### **2. Generate Predictions**
```python
from datetime import datetime, timedelta

start_date = datetime.now()
end_date = start_date + timedelta(days=90)

prediction_result = await engine.predict_cash_flow(start_date, end_date)
```

### **3. Access Results**
```python
# Daily predictions
daily_predictions = prediction_result["predictions"]["daily_predictions"]

# Scenarios
scenarios = prediction_result["scenarios"]
base_case = scenarios["base_case"]
pessimistic = scenarios["pessimistic"]

# Insights
insights = prediction_result["insights"]
risk_factors = insights["risk_factors"]
recommendations = insights["recommendations"]
```

## 🎛️ Advanced Features

### **1. Machine Learning Models**
- **Linear Regression** for trend analysis
- **Random Forest** for non-linear patterns
- **Ensemble methods** for improved accuracy
- **Automatic retraining** based on new data

### **2. Data Quality Assessment**
```python
data_quality = prediction_result["data_quality"]
print(f"Overall Quality Score: {data_quality['overall_score']}/100")
print(f"Operational Data Quality: {data_quality['operational_data_quality']['score']}/100")
print(f"Planning Data Quality: {data_quality['planning_data_quality']['score']}/100")
```

### **3. Prediction Components Breakdown**
```python
daily_prediction = prediction_result["predictions"]["daily_predictions"][0]
components = daily_prediction["prediction_components"]

print(f"Customer Payments: ${components['customer_payments']}")
print(f"Supplier Payments: ${components['supplier_payments']}")
print(f"Payroll: ${components['payroll_payments']}")
print(f"Operating Expenses: ${components['operating_expenses']}")
print(f"Capital Expenditure: ${components['capital_expenditure']}")
```

## 🚀 Deployment

### **1. Railway Deployment**
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://..."
export EXCEL_DATA_PATH="/app/business-planning"

# Start API server
python cash_flow_api.py
```

### **2. Docker Deployment**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "cash_flow_api.py"]
```

### **3. Integration with EZBI Platform**
```typescript
// Add to your EZBI platform
const response = await fetch('/api/v1/cash-flow-dashboard');
const dashboardData = await response.json();

// Use dashboard data in your components
<CashFlowDashboard data={dashboardData} />
```

## 📊 Performance Metrics

### **Expected Accuracy**:
- **70-85%** prediction accuracy for 30-day forecasts
- **60-75%** accuracy for 90-day forecasts
- **Confidence intervals** provide uncertainty bounds

### **Data Processing**:
- **< 2 seconds** for quick predictions
- **< 5 seconds** for full dashboard generation
- **< 10 seconds** for scenario analysis

### **Scalability**:
- **Concurrent requests** supported via async architecture
- **Connection pooling** for database efficiency
- **Background tasks** for heavy operations

## 🔧 Maintenance

### **1. Model Retraining**
Models automatically retrain every 7 days when new data is available:
```python
if engine._should_retrain_models():
    await engine._train_prediction_models(historical_data, operational_data, planning_data)
```

### **2. Data Refresh**
Excel business planning files can be regenerated:
```bash
POST /api/v1/regenerate-business-planning
```

### **3. Health Monitoring**
```bash
GET /health
GET /api/v1/model-performance
GET /api/v1/business-planning-status
```

This cash flow prediction engine provides manufacturers with accurate, data-driven cash flow forecasts by intelligently combining operational history with business planning data, enabling proactive financial management and strategic decision-making.