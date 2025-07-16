"""Scheduler configuration for Railway deployment"""

import os
from datetime import datetime

# Scheduler configuration
SCHEDULER_CONFIG = {
    'job_defaults': {
        'coalesce': True,
        'max_instances': 3,
        'misfire_grace_time': 3600  # 1 hour grace period
    },
    'executors': {
        'default': {
            'type': 'threadpool',
            'max_workers': 20
        }
    },
    'timezone': os.getenv('TZ', 'UTC')
}

# Job configurations - runs daily at specified times (UTC)
DAILY_JOBS = {
    'generate_daily_transactions': {
        'hour': 0,
        'minute': 30,
        'description': 'Generate daily transaction records'
    },
    'generate_daily_invoices': {
        'hour': 1,
        'minute': 0,
        'description': 'Generate new sales invoices'
    },
    'update_accounts_receivable': {
        'hour': 1,
        'minute': 30,
        'description': 'Update accounts receivable aging'
    },
    'generate_daily_purchases': {
        'hour': 2,
        'minute': 0,
        'description': 'Generate new purchase orders'
    },
    'update_accounts_payable': {
        'hour': 2,
        'minute': 30,
        'description': 'Update accounts payable'
    },
    'process_payroll': {
        'hour': 3,
        'minute': 0,
        'description': 'Process bi-weekly/monthly payroll when due'
    },
    'update_cash_ledger': {
        'hour': 3,
        'minute': 30,
        'description': 'Update cash ledger with daily transactions'
    },
    'generate_production_orders': {
        'hour': 4,
        'minute': 0,
        'description': 'Generate new production orders'
    },
    'update_debt_payments': {
        'hour': 4,
        'minute': 30,
        'description': 'Process debt account payments'
    },
    'generate_ai_predictions': {
        'hour': 5,
        'minute': 0,
        'description': 'Generate new AI predictions for next 30 days'
    },
    'cleanup_old_data': {
        'hour': 23,
        'minute': 0,
        'description': 'Archive old data beyond retention period'
    }
}

# Data generation limits per day
DAILY_LIMITS = {
    'transactions_per_company': (5, 20),  # Min, Max per company
    'invoices_per_day': (10, 30),
    'purchases_per_day': (5, 15),
    'production_orders_per_day': (3, 10),
    'predictions_days_ahead': 30
}

# Railway-specific settings
RAILWAY_ENV = os.getenv('RAILWAY_ENVIRONMENT', 'development')
ENABLE_SCHEDULER = os.getenv('ENABLE_SCHEDULER', 'true').lower() == 'true'
SCHEDULER_LOG_LEVEL = os.getenv('SCHEDULER_LOG_LEVEL', 'INFO')