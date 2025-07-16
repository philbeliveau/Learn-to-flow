# Data Generation Scheduler for EZBI Analytics

This scheduler automatically populates your manufacturing database with realistic data on a daily basis.

## Overview

The scheduler runs 11 different jobs throughout the day to simulate a real manufacturing business:

1. **Daily Transactions** (00:30 UTC) - Generates 5-20 transactions per company
2. **Sales Invoices** (01:00 UTC) - Creates 10-30 new invoices
3. **Accounts Receivable** (01:30 UTC) - Updates AR aging buckets
4. **Purchase Orders** (02:00 UTC) - Generates 5-15 vendor purchases
5. **Accounts Payable** (02:30 UTC) - Updates AP records
6. **Payroll Processing** (03:00 UTC) - Processes bi-weekly/monthly payroll
7. **Cash Ledger** (03:30 UTC) - Updates cash flow transactions
8. **Production Orders** (04:00 UTC) - Creates 3-10 new production orders
9. **Debt Payments** (04:30 UTC) - Processes loan payments
10. **AI Predictions** (05:00 UTC) - Generates 30-day forecasts
11. **Data Cleanup** (23:00 UTC) - Archives old data

## Local Development

### Running Without Scheduler
```bash
# Set environment variable to disable scheduler
export ENABLE_SCHEDULER=false
python app_flask.py
```

### Testing Scheduler Locally
```bash
# Enable scheduler
export ENABLE_SCHEDULER=true
python app_flask.py
```

### Manual Job Execution

You can trigger jobs manually via API:

```bash
# Run a specific job
curl -X POST http://localhost:8003/api/scheduler/jobs/generate_daily_transactions/run

# Run all jobs at once (useful for testing)
curl -X POST http://localhost:8003/api/scheduler/run-all

# Check scheduler status
curl http://localhost:8003/api/scheduler/status

# Get all scheduled jobs
curl http://localhost:8003/api/scheduler/jobs
```

## Railway Deployment

### Environment Variables

Set these in your Railway project:

```bash
ENABLE_SCHEDULER=true
RAILWAY_ENVIRONMENT=production
TZ=UTC
DATABASE_PATH=data/ezbi_analytics.db
SCHEDULER_LOG_LEVEL=INFO
```

### Deployment Steps

1. **DO NOT deploy yet** - The backend is ready but not deployed
2. When you're ready to deploy:
   - Push your code to GitHub
   - Connect Railway to your GitHub repo
   - Railway will auto-detect the Flask app
   - Set the environment variables above
   - Deploy!

### Monitoring

Once deployed, you can monitor the scheduler:

```bash
# Check scheduler status
curl https://your-app.railway.app/api/scheduler/status

# View scheduled jobs
curl https://your-app.railway.app/api/scheduler/jobs

# Check logs in Railway dashboard for job execution
```

## API Endpoints

### Scheduler Management

- `GET /api/scheduler/status` - Get scheduler status
- `GET /api/scheduler/jobs` - List all scheduled jobs
- `POST /api/scheduler/jobs/{job_id}/run` - Run a specific job
- `POST /api/scheduler/jobs/{job_id}/pause` - Pause a job
- `POST /api/scheduler/jobs/{job_id}/resume` - Resume a job
- `POST /api/scheduler/run-all` - Run all jobs immediately
- `GET /api/scheduler/config` - Get scheduler configuration

## Data Generation Details

### Transaction Generation
- Each company gets 5-20 transactions daily
- Types: income, expense, transfer, investment, loan_payment
- Realistic amounts based on transaction type

### Invoice Generation
- 10-30 new invoices daily
- Linked to existing customers and products
- Automatic status updates (Open → Overdue)

### Payroll Processing
- Bi-weekly or monthly based on employee settings
- Includes overtime and bonus calculations
- Automatic deduction calculations

### Production Orders
- 3-10 new orders daily
- Progress tracking for existing orders
- Cost calculations on completion

### AI Predictions
- 30-day forecasts for each company
- Multiple model types (linear regression, random forest, etc.)
- Confidence scores decrease with forecast horizon

## Troubleshooting

### Scheduler Not Running
1. Check `ENABLE_SCHEDULER` environment variable
2. Check logs for initialization errors
3. Verify database path is correct

### Jobs Failing
1. Check individual job logs
2. Verify database tables exist
3. Check foreign key constraints

### Performance Issues
1. Monitor job execution times
2. Adjust daily limits in configuration
3. Consider running cleanup more frequently

## Security Notes

- The scheduler only generates fake data
- No sensitive information is created
- All passwords in test data are hashed
- Data retention policies prevent unlimited growth