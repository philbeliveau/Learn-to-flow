# Excel Data Source Integration

## 📋 Overview

This module implements **Excel files as data sources** for the EZBI platform, combining database simulation with Excel-based data ingestion for dashboard visualization.

## 🏗️ Updated Architecture

### **Data Flow**:
```
PostgreSQL Database → Daily Simulator → Excel Data Source → EZBI Platform → Dashboard + Slack
```

### **Key Components**:
1. **`excel_data_source.py`** - Generates Excel files as structured data sources
2. **`ezbi_excel_reader.py`** - Reads and processes Excel files for EZBI platform
3. **`updated_workflow.py`** - Orchestrates the complete workflow

## 📊 Excel Data Source Structure

### **Generated Files**:
```
manufacturing_data_source_20240115.xlsx
├── 📄 metadata (Processing information)
├── 📄 dashboard (Summary metrics)
├── 📄 invoices (B2B sales data)
├── 📄 cash_flow (Financial transactions)
├── 📄 ar_aging (Collections data)
├── 📄 production (Manufacturing orders)
├── 📄 purchases (Vendor transactions)
├── 📄 payroll (Employee payments)
└── 📄 kpis (Key performance indicators)

manufacturing_data_source_20240115.json (Metadata)
```

### **Excel Sheet Examples**:

**Dashboard Sheet**:
```
metric              | value      | date       | category
cash_balance       | 125000.00  | 2024-01-15 | financial
daily_sales        | 45000.00   | 2024-01-15 | sales
outstanding_ar     | 89000.00   | 2024-01-15 | collections
```

**Invoices Sheet**:
```
invoice_id | customer_name        | amount    | date_issued | days_overdue
1001      | AutoParts Manufacturing | 15000.00 | 2024-01-15 | 0
1002      | Industrial Solutions    | 22000.00 | 2024-01-15 | 0
```

**Cash Flow Sheet**:
```
transaction_id | amount    | transaction_type | flow_direction | counterparty
5001          | 15000.00  | Sale            | Inflow        | Customer-1
5002          | -3000.00  | Purchase        | Outflow       | Steel Supplier
```

## 🔄 Daily Workflow Process

### **Step 1: Generate Excel Data Source**
```python
# From database to Excel
excel_file_path = await excel_data_source.generate_daily_data_source(db_connection, date)
```

### **Step 2: Process Excel for EZBI Platform**
```python
# Read and transform Excel data
processing_report = await ezbi_reader.process_excel_data_source(excel_file_path)
dashboard_data = processing_report['dashboard_data']
```

### **Step 3: Update EZBI Dashboard**
```python
# Send processed data to EZBI platform
response = await client.post(
    f"{ezbi_api_url}/api/v1/dashboard/manufacturing/update",
    json={'dashboard_data': dashboard_data}
)
```

### **Step 4: Send Slack Notification**
```python
# Notify team of updated data
await send_slack_notification(workflow_report, dashboard_data)
```

## 🎯 EZBI Platform Integration

### **New API Endpoints** (Add to your EZBI platform):

**1. Dashboard Update Endpoint**:
```typescript
// pages/api/v1/dashboard/manufacturing/update.ts
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    const { dashboard_data } = req.body;
    
    // Update dashboard with Excel data
    await updateManufacturingDashboard(dashboard_data);
    
    res.status(200).json({ success: true });
  }
}
```

**2. Excel Data Ingestion Endpoint**:
```typescript
// pages/api/v1/data/excel/ingest.ts
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    const excelData = req.body;
    
    // Process Excel data for charts
    const chartData = await processExcelForCharts(excelData);
    
    // Update database
    await storeExcelData(excelData);
    
    res.status(200).json({ success: true, charts: chartData });
  }
}
```

### **Dashboard Components** (Add to your EZBI platform):

**1. Manufacturing Dashboard**:
```typescript
// components/ManufacturingDashboard.tsx
import { useEffect, useState } from 'react';
import { Chart } from 'chart.js/auto';

export const ManufacturingDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  
  useEffect(() => {
    // Fetch latest Excel data
    fetchManufacturingData();
  }, []);
  
  const fetchManufacturingData = async () => {
    const response = await fetch('/api/v1/dashboard/manufacturing/latest');
    const data = await response.json();
    setDashboardData(data);
  };
  
  return (
    <div className="manufacturing-dashboard">
      <h2>Manufacturing Business Analytics</h2>
      
      {/* KPI Cards */}
      <div className="kpi-grid">
        {dashboardData?.kpis?.map(kpi => (
          <KPICard key={kpi.name} kpi={kpi} />
        ))}
      </div>
      
      {/* Charts */}
      <div className="charts-grid">
        {dashboardData?.charts?.map(chart => (
          <ChartWidget key={chart.title} config={chart} />
        ))}
      </div>
      
      {/* Data Tables */}
      <div className="tables-section">
        {dashboardData?.tables?.map(table => (
          <DataTable key={table.title} config={table} />
        ))}
      </div>
    </div>
  );
};
```

**2. Excel Data File Monitor**:
```typescript
// components/ExcelDataMonitor.tsx
export const ExcelDataMonitor = () => {
  const [dataFiles, setDataFiles] = useState([]);
  
  useEffect(() => {
    const interval = setInterval(checkForNewData, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);
  
  const checkForNewData = async () => {
    const response = await fetch('/api/v1/data/excel/list');
    const files = await response.json();
    setDataFiles(files);
    
    // Check for new files and auto-process
    const newFiles = files.filter(file => !file.processed);
    for (const file of newFiles) {
      await processExcelFile(file);
    }
  };
  
  return (
    <div className="excel-data-monitor">
      <h3>Excel Data Sources</h3>
      <ul>
        {dataFiles.map(file => (
          <li key={file.filename}>
            {file.filename} - {file.generated_date}
            <span className={file.processed ? 'processed' : 'pending'}>
              {file.processed ? '✅ Processed' : '⏳ Pending'}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};
```

## 🎨 Chart Configurations

### **Cash Flow Chart**:
```javascript
{
  type: 'bar',
  title: 'Daily Cash Flow',
  data: {
    labels: ['Inflows', 'Outflows'],
    datasets: [{
      data: [125000, 89000],
      backgroundColor: ['#10B981', '#EF4444']
    }]
  }
}
```

### **AR Aging Chart**:
```javascript
{
  type: 'doughnut',
  title: 'Accounts Receivable Aging',
  data: {
    labels: ['0-30 days', '31-60 days', '61-90 days', '90+ days'],
    datasets: [{
      data: [45000, 15000, 8000, 21000],
      backgroundColor: ['#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
    }]
  }
}
```

## 📝 Updated Slack Notifications

### **Daily Summary Message**:
```
📊 Manufacturing Data Workflow Complete - 2024-01-15

✅ Workflow Status: Completed
   • Steps Completed: 5/5
   • Excel Data Source: ✅ Generated and processed
   • EZBI Dashboard: ✅ Updated with latest data
   • Charts Generated: 4 charts

📊 Key Performance Indicators
   • 💰 Cash Position: $125,000.00
   • 💵 Daily Sales: $45,000.00
```

## 🔧 Configuration

### **Environment Variables**:
```env
# EZBI Platform Integration
EZBI_API_URL=https://your-ezbi-platform.vercel.app
EZBI_API_KEY=your-api-key-here

# Excel Data Source
EXCEL_EXPORT_PATH=/app/exports
EZBI_DATA_PATH=/app/data-sources

# Workflow Configuration
AUTO_PROCESS_EXCEL=true
UPDATE_EZBI_DASHBOARD=true
CLEANUP_OLD_FILES=true
RETENTION_DAYS=30
```

### **Workflow Configuration**:
```python
WORKFLOW_CONFIG = {
    'excel_export_path': '/app/exports',
    'ezbi_data_path': '/app/data-sources',
    'ezbi_api_url': os.getenv('EZBI_API_URL'),
    'ezbi_api_key': os.getenv('EZBI_API_KEY'),
    'slack_webhook_url': os.getenv('SLACK_WEBHOOK_URL')
}
```

## 🚀 Deployment Integration

### **Update main.py** (Add to your Railway service):
```python
# Import updated workflow
from updated_workflow import create_manufacturing_workflow, WORKFLOW_CONFIG

# Add to your FastAPI app
@app.post("/workflow/run")
async def run_workflow():
    workflow = create_manufacturing_workflow(WORKFLOW_CONFIG)
    result = await workflow.run_daily_workflow(db_connection)
    return result

# Update daily simulation to use new workflow
async def run_daily_simulation():
    workflow = create_manufacturing_workflow(WORKFLOW_CONFIG)
    return await workflow.run_daily_workflow(db_connection)
```

### **Update requirements.txt**:
```txt
# Add these to your existing requirements.txt
openpyxl==3.1.2
xlsxwriter==3.1.9
pandas==2.1.4
numpy==1.24.4
```

## 🎯 Benefits of Excel Data Source Approach

1. **Business-Friendly**: Users can review/edit Excel files before processing
2. **Flexible Integration**: EZBI platform can easily consume Excel format
3. **Version Control**: Each day creates timestamped Excel files
4. **Backup**: Excel files serve as data backups
5. **Debugging**: Easy to inspect Excel files for data quality
6. **Scalability**: Can handle large datasets efficiently
7. **Chart-Ready**: Data pre-formatted for visualization

## 📊 Example Usage

### **Generate Daily Data Source**:
```python
from excel_data_source import create_excel_data_source

# Create Excel data source
excel_source = create_excel_data_source('/app/exports')

# Generate daily file
excel_file = await excel_source.generate_daily_data_source(db_connection, datetime.now())
```

### **Process for EZBI Platform**:
```python
from ezbi_excel_reader import create_ezbi_excel_reader

# Create Excel reader
ezbi_reader = create_ezbi_excel_reader('/app/data-sources')

# Process Excel file
dashboard_data = await ezbi_reader.process_excel_data_source(excel_file)
```

### **Run Complete Workflow**:
```python
from updated_workflow import create_manufacturing_workflow

# Create workflow
workflow = create_manufacturing_workflow(WORKFLOW_CONFIG)

# Run daily workflow
result = await workflow.run_daily_workflow(db_connection)
```

This updated implementation provides a robust Excel-based data source system that integrates seamlessly with your EZBI platform while maintaining the benefits of database simulation and comprehensive business reporting.