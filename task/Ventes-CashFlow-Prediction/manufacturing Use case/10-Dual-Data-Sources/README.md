# Dual Data Sources Architecture

## 🎯 Overview

This implementation creates **two completely separate data sources** that your EZBI platform extracts from:

1. **PostgreSQL Database** - Direct extraction of manufacturing operational data
2. **Excel Files** - Separate market research and industry intelligence data

Both data sources feed into a unified dashboard with strategic insights.

## 🏗️ Architecture

### **Data Flow**:
```
Manufacturing Simulator → PostgreSQL Database ← EZBI Platform (Direct SQL extraction)
                                                     ↓
                                              Unified Dashboard
                                                     ↑
Market Research Generator → Excel Files ← EZBI Platform (File-based extraction)
```

### **Key Components**:

1. **`postgres_direct_extractor.py`** - Direct PostgreSQL data extraction
2. **`separate_excel_data_source.py`** - Market research Excel generator
3. **`dual_dashboard_integration.py`** - Unified dashboard integration
4. **`README.md`** - Implementation guide

## 📊 Data Source Details

### **PostgreSQL Data Source** (Manufacturing Operations):
- **Direct SQL queries** to extract operational data
- **Real-time metrics** for live dashboard updates
- **Financial data**: Cash flow, AR aging, vendor payments
- **Operational data**: Production orders, efficiency metrics
- **Customer data**: Sales performance, payment patterns

### **Excel Data Source** (Market Intelligence):
- **Market research data** in structured Excel format
- **Industry trends** and competitive landscape
- **Economic indicators** and technology adoption
- **Supply chain insights** and regulatory updates
- **Customer insights** and forecast models

## 🔄 Daily Workflow

### **Step 1: PostgreSQL Data Extraction**
```python
# Extract operational data directly from database
dashboard_data = await postgres_extractor.extract_dashboard_data(start_date, end_date)
```

### **Step 2: Excel Data Generation**
```python
# Generate market research Excel file
excel_file = market_research_source.generate_market_research_excel(date)
```

### **Step 3: Unified Dashboard Integration**
```python
# Combine both data sources
unified_data = await dual_integration.extract_unified_dashboard_data()
```

### **Step 4: Strategic Analysis**
```python
# Generate combined insights
combined_insights = await dual_integration._combine_data_sources(postgres_data, excel_data)
```

## 📈 Dashboard Structure

### **4-Section Dashboard Layout**:

#### **1. Executive Overview**
- **KPIs from both sources**: Cash balance, market size, growth rates
- **Data sources**: PostgreSQL + Excel
- **Charts**: Combined performance indicators

#### **2. Financial Performance** 
- **PostgreSQL data**: Cash flow trends, AR aging, financial KPIs
- **Charts**: Cash flow line chart, AR aging doughnut, sales performance
- **Real-time updates**: Live financial metrics

#### **3. Market Intelligence**
- **Excel data**: Market trends, competitive landscape, economic indicators
- **Charts**: Market opportunity matrix, economic trends, competitor analysis
- **Updates**: Daily market research refresh

#### **4. Strategic Insights**
- **Combined analysis**: Business performance vs market trends
- **Risk assessment**: Financial + market risks
- **Growth opportunities**: Operational + market opportunities
- **Competitive positioning**: Company vs industry benchmarks

## 🎨 Chart Examples

### **PostgreSQL Charts**:
```javascript
// Cash Flow Trend (from PostgreSQL)
{
  type: 'line',
  title: 'Daily Cash Flow Trend',
  data: {
    labels: ['2024-01-01', '2024-01-02', '2024-01-03'],
    datasets: [{
      label: 'Inflows',
      data: [125000, 89000, 156000],
      borderColor: '#10B981'
    }]
  }
}

// AR Aging (from PostgreSQL)
{
  type: 'doughnut',
  title: 'Accounts Receivable Aging',
  data: {
    labels: ['0-30', '31-60', '61-90', '90+'],
    datasets: [{
      data: [45000, 15000, 8000, 21000],
      backgroundColor: ['#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
    }]
  }
}
```

### **Excel Charts**:
```javascript
// Market Opportunity Matrix (from Excel)
{
  type: 'bubble',
  title: 'Market Size vs Growth Rate by Sector',
  data: {
    datasets: [{
      data: [
        {x: 12.5, y: 45.2, r: 25, label: 'Automotive'},
        {x: 8.3, y: 89.1, r: 35, label: 'Aerospace'}
      ]
    }]
  }
}

// Economic Indicators (from Excel)
{
  type: 'line',
  title: 'Economic Indicators Trend',
  data: {
    labels: ['2024-01-01', '2024-01-02', '2024-01-03'],
    datasets: [{
      label: 'Manufacturing PMI',
      data: [52.3, 53.1, 51.8],
      borderColor: '#FF6384'
    }]
  }
}
```

## 💡 EZBI Platform Integration

### **New API Endpoints** (Add to your EZBI platform):

#### **1. Dual Data Extraction Endpoint**:
```typescript
// pages/api/v1/dashboard/dual-extract.ts
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    // Extract from PostgreSQL
    const postgresData = await extractPostgreSQLData();
    
    // Process Excel files
    const excelData = await processLatestExcelFiles();
    
    // Combine data sources
    const unifiedData = await combineDataSources(postgresData, excelData);
    
    res.status(200).json(unifiedData);
  } catch (error) {
    res.status(500).json({ error: 'Data extraction failed' });
  }
}
```

#### **2. Real-time Updates Endpoint**:
```typescript
// pages/api/v1/dashboard/real-time.ts
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    // Get real-time PostgreSQL metrics
    const realTimeData = await getRealTimeMetrics();
    
    // Check for new Excel files
    const excelUpdates = await checkExcelUpdates();
    
    res.status(200).json({
      timestamp: new Date().toISOString(),
      postgres_metrics: realTimeData,
      excel_updates: excelUpdates
    });
  } catch (error) {
    res.status(500).json({ error: 'Real-time update failed' });
  }
}
```

### **Dashboard Components** (Add to your EZBI platform):

#### **1. Unified Dashboard Component**:
```typescript
// components/UnifiedDashboard.tsx
import React, { useState, useEffect } from 'react';

export const UnifiedDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchUnifiedData();
    
    // Set up real-time updates
    const interval = setInterval(fetchRealTimeUpdates, 30000); // 30 seconds
    return () => clearInterval(interval);
  }, []);
  
  const fetchUnifiedData = async () => {
    try {
      const response = await fetch('/api/v1/dashboard/dual-extract');
      const data = await response.json();
      setDashboardData(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch unified data:', error);
    }
  };
  
  const fetchRealTimeUpdates = async () => {
    try {
      const response = await fetch('/api/v1/dashboard/real-time');
      const updates = await response.json();
      
      // Update specific metrics without full reload
      setDashboardData(prev => ({
        ...prev,
        postgres_data: {
          ...prev.postgres_data,
          real_time_metrics: updates.postgres_metrics
        }
      }));
    } catch (error) {
      console.error('Failed to fetch real-time updates:', error);
    }
  };
  
  if (loading) return <div>Loading unified dashboard...</div>;
  
  return (
    <div className="unified-dashboard">
      {/* Executive Overview Section */}
      <section className="overview-section">
        <h2>Executive Overview</h2>
        <div className="kpi-grid">
          {dashboardData?.dashboard_layout?.sections?.overview?.kpis?.map(kpi => (
            <KPICard key={kpi.name} kpi={kpi} />
          ))}
        </div>
      </section>
      
      {/* Financial Performance Section */}
      <section className="financial-section">
        <h2>Financial Performance</h2>
        <div className="charts-grid">
          {dashboardData?.postgres_data?.charts?.map(chart => (
            <ChartWidget key={chart.title} config={chart} />
          ))}
        </div>
      </section>
      
      {/* Market Intelligence Section */}
      <section className="market-section">
        <h2>Market Intelligence</h2>
        <div className="charts-grid">
          {dashboardData?.excel_data?.charts?.map(chart => (
            <ChartWidget key={chart.title} config={chart} />
          ))}
        </div>
      </section>
      
      {/* Strategic Insights Section */}
      <section className="strategic-section">
        <h2>Strategic Insights</h2>
        <div className="insights-grid">
          <CombinedAnalysisWidget data={dashboardData?.combined_data} />
          <RiskAssessmentWidget risks={dashboardData?.combined_data?.risk_assessment} />
          <GrowthOpportunitiesWidget opportunities={dashboardData?.combined_data?.growth_opportunities} />
        </div>
      </section>
    </div>
  );
};
```

#### **2. Data Source Monitor**:
```typescript
// components/DataSourceMonitor.tsx
export const DataSourceMonitor: React.FC = () => {
  const [dataSourceHealth, setDataSourceHealth] = useState(null);
  
  useEffect(() => {
    const checkHealth = async () => {
      const response = await fetch('/api/v1/dashboard/health-check');
      const health = await response.json();
      setDataSourceHealth(health);
    };
    
    checkHealth();
    const interval = setInterval(checkHealth, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);
  
  return (
    <div className="data-source-monitor">
      <h3>Data Source Health</h3>
      
      <div className="source-status">
        <div className="postgresql-status">
          <h4>PostgreSQL Database</h4>
          <span className={`status ${dataSourceHealth?.postgres_health?.status}`}>
            {dataSourceHealth?.postgres_health?.status}
          </span>
          <p>Manufacturing operational data</p>
        </div>
        
        <div className="excel-status">
          <h4>Excel Market Research</h4>
          <span className={`status ${dataSourceHealth?.excel_health?.status}`}>
            {dataSourceHealth?.excel_health?.status}
          </span>
          <p>Market intelligence data</p>
        </div>
      </div>
    </div>
  );
};
```

## 🔧 Configuration

### **Environment Variables**:
```env
# PostgreSQL Direct Extraction
DATABASE_URL=postgresql://user:pass@host:port/database

# Excel Data Source
EXCEL_MARKET_DATA_PATH=/app/market-data
EXCEL_GENERATION_SCHEDULE=0 7 * * *

# Dual Integration
DASHBOARD_REFRESH_INTERVAL=15
POSTGRES_DATA_WEIGHT=0.6
EXCEL_DATA_WEIGHT=0.4
```

### **Railway Deployment**:
```python
# Add to main.py
from dual_dashboard_integration import create_dual_dashboard_integration

# Initialize dual integration
dual_integration = create_dual_dashboard_integration(
    postgres_url=DATABASE_URL,
    excel_path="/app/market-data"
)

@app.get("/api/v1/dashboard/unified")
async def get_unified_dashboard():
    return await dual_integration.extract_unified_dashboard_data()

@app.get("/api/v1/dashboard/real-time")
async def get_real_time_update():
    return await dual_integration.get_real_time_update()
```

## 🚀 Benefits

### **1. Data Diversity**:
- **Operational data** from PostgreSQL (internal metrics)
- **Market intelligence** from Excel (external insights)
- **Combined analysis** for strategic decisions

### **2. Real-time + Batch Processing**:
- **PostgreSQL**: Real-time queries for operational metrics
- **Excel**: Daily batch processing for market research
- **Unified dashboard**: Both data sources integrated

### **3. Scalability**:
- **PostgreSQL**: Handles high-volume transactional data
- **Excel**: Manages complex market research datasets
- **Independent scaling** of each data source

### **4. Business Value**:
- **Operational insights**: How is the business performing?
- **Market context**: What's happening in the industry?
- **Strategic guidance**: Where should we focus next?

## 📊 Example Usage

### **Extract Unified Dashboard Data**:
```python
from dual_dashboard_integration import create_dual_dashboard_integration

# Create integration
dual_integration = create_dual_dashboard_integration(DATABASE_URL)

# Extract unified data
unified_data = await dual_integration.extract_unified_dashboard_data()

# Access different data sources
postgres_charts = unified_data['postgres_data']['charts']
excel_charts = unified_data['excel_data']['charts']
combined_insights = unified_data['combined_data']
```

### **Real-time Updates**:
```python
# Get real-time metrics
real_time_data = await dual_integration.get_real_time_update()

# Check data source health
health_status = await dual_integration.health_check()
```

This dual data source architecture provides comprehensive business intelligence by combining internal operational data with external market research, giving you both operational insights and strategic market context in a unified dashboard.