# Database Schema Design

## 🗄️ PostgreSQL Schema Structure

The manufacturing use case database is organized into 6 logical schemas:

### Schema Organization
- **`sales`** - Customer management and invoicing
- **`accounting`** - AR/AP and vendor management  
- **`operations`** - Production and inventory management
- **`finance`** - Cash flow and debt management
- **`expenses`** - Fixed costs and expense tracking
- **`hr`** - Employee and payroll management

## 📊 Core Tables Overview

### 1. Sales Domain
- `sales.customers` - B2B customer database
- `sales.invoices` - Invoice tracking with Net-30 terms

### 2. Accounting Domain  
- `accounting.accounts_receivable` - AR aging buckets
- `accounting.vendors` - Supplier management
- `accounting.purchases` - Purchase order tracking
- `accounting.accounts_payable` - AP aging and due dates

### 3. Operations Domain
- `operations.products` - Product catalog with costs
- `operations.production_orders` - Manufacturing workflow

### 4. Finance Domain
- `finance.cash_ledger` - Daily transaction log
- `finance.debt_accounts` - Loan and credit management
- `finance.debt_payments` - Payment history

### 5. Expenses Domain
- `expenses.fixed_costs` - Scheduled recurring expenses
- `expenses.expense_log` - Payment history

### 6. HR Domain
- `hr.employees` - Employee database
- `hr.payroll_log` - Bi-weekly payroll records

## 🔗 Key Relationships

### Customer Flow
```
customers → invoices → accounts_receivable → cash_ledger
```

### Production Flow
```
products → production_orders → cost_of_goods_sold → cash_ledger
```

### Vendor Flow
```
vendors → purchases → accounts_payable → cash_ledger
```

## 📈 Data Volume Estimates

Daily generation targets:
- **Invoices**: 1-3 per day
- **Production Orders**: 0-2 per day  
- **Purchases**: 2-5 per day
- **Cash Transactions**: 10-15 per day
- **Payroll**: Every 14 days
- **Fixed Expenses**: Monthly schedule

## 🎯 Business Rules Implemented

### AR Aging Buckets
- 0-30 days: Current
- 31-60 days: Past due
- 61-90 days: Seriously past due  
- 90+ days: Collections risk

### Payment Terms
- Customer invoices: Net-30 standard
- Vendor purchases: Net-15 to Net-30
- Employee payroll: Bi-weekly schedule

### Production Workflow
- Orders start in "Planned" status
- Move to "In Progress" when started
- Complete with actual costs recorded
- Variable completion times (1-5 days)

## 🔧 Performance Optimizations

### Indexes Created
- Customer and date-based invoice lookups
- AR aging bucket queries
- Cash ledger date and type filtering
- Production order status tracking
- Vendor purchase history

### Query Patterns
- Daily cash position calculation
- AR aging reports
- Production status dashboard
- Vendor payment schedules