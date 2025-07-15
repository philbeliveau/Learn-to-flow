# Manufacturing Use Case - Project Overview

## 🎯 Objective
Create a production-grade synthetic data generator simulating a mid-sized manufacturing company with realistic daily business operations, integrated with the EZBI Analytics platform for real-time visualization and Slack notifications.

## 🏭 Simulated Company Profile
- **Business Type**: Mid-sized manufacturing company
- **Product**: Custom metal parts
- **Sales Model**: B2B with Net-30 payment terms
- **Production**: Made-to-order (MTO), small batches
- **Operating Schedule**: Daily operations, bi-weekly payroll, monthly fixed costs

## 🏗️ Architecture Overview

### Hosting Strategy
- **Data Generator**: Railway (Python FastAPI service)
- **Database**: Railway PostgreSQL
- **Platform Frontend**: Vercel (existing EZBI platform)
- **File Storage**: Railway persistent volumes for Excel exports
- **Notifications**: Slack integration via webhooks

### Data Flow
```
Daily Simulator (Railway) 
    ↓
PostgreSQL (Railway)
    ↓
EZBI Platform (Vercel) → Slack Notifications
    ↓
Excel Exports (Railway Storage)
```

## 📊 Data Domains (8 Core Areas)
1. **Sales & Invoices** - B2B transactions with payment terms
2. **Accounts Receivable** - AR aging and collections
3. **Production Orders** - Manufacturing workflow tracking
4. **Purchases & AP** - Vendor payments and supplies
5. **Cash Flow Ledger** - Daily bank-like transactions
6. **Debt & Financing** - Loans and credit management
7. **Fixed Costs (OPEX)** - Rent, utilities, licenses
8. **HR & Payroll** - Employee payments and schedules

## 🎯 Success Metrics
- Daily generation of 50-100 realistic business transactions
- Real-time data visualization in EZBI platform
- Daily Slack summaries with key metrics
- Excel exports for business user consumption
- 99.9% uptime on Railway hosting

## 📅 Implementation Timeline
- **Phase 1**: Database schema and core simulator (Week 1)
- **Phase 2**: Railway deployment and API integration (Week 2)
- **Phase 3**: EZBI platform integration and visualization (Week 3)
- **Phase 4**: Slack notifications and Excel exports (Week 4)

## 🔗 Integration Points
- **EZBI API**: Real-time data ingestion endpoints
- **Slack Webhook**: Daily summary notifications
- **Excel API**: Automated report generation
- **Railway Cron**: Daily simulation scheduling