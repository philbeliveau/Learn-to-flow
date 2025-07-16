"""APScheduler integration for Flask"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from .config import SCHEDULER_CONFIG, DAILY_JOBS, ENABLE_SCHEDULER
from .jobs import (
    generate_daily_transactions_job,
    generate_daily_invoices_job,
    update_accounts_receivable_job,
    generate_daily_purchases_job,
    update_accounts_payable_job,
    process_payroll_job,
    update_cash_ledger_job,
    generate_production_orders_job,
    update_debt_payments_job,
    generate_ai_predictions_job,
    cleanup_old_data_job
)

logger = logging.getLogger(__name__)

class DataScheduler:
    def __init__(self):
        self.scheduler = None
        self.jobs_map = {
            'generate_daily_transactions': generate_daily_transactions_job,
            'generate_daily_invoices': generate_daily_invoices_job,
            'update_accounts_receivable': update_accounts_receivable_job,
            'generate_daily_purchases': generate_daily_purchases_job,
            'update_accounts_payable': update_accounts_payable_job,
            'process_payroll': process_payroll_job,
            'update_cash_ledger': update_cash_ledger_job,
            'generate_production_orders': generate_production_orders_job,
            'update_debt_payments': update_debt_payments_job,
            'generate_ai_predictions': generate_ai_predictions_job,
            'cleanup_old_data': cleanup_old_data_job
        }
    
    def init_scheduler(self, app):
        """Initialize scheduler with Flask app context"""
        if not ENABLE_SCHEDULER:
            logger.info("Scheduler is disabled via ENABLE_SCHEDULER environment variable")
            return
        
        self.scheduler = BackgroundScheduler(**SCHEDULER_CONFIG)
        
        # Add all daily jobs
        for job_name, job_config in DAILY_JOBS.items():
            if job_name in self.jobs_map:
                trigger = CronTrigger(
                    hour=job_config['hour'],
                    minute=job_config['minute'],
                    timezone=SCHEDULER_CONFIG['timezone']
                )
                
                self.scheduler.add_job(
                    func=self.jobs_map[job_name],
                    trigger=trigger,
                    id=job_name,
                    name=job_config['description'],
                    replace_existing=True
                )
                logger.info(f"Scheduled job: {job_name} at {job_config['hour']:02d}:{job_config['minute']:02d} UTC")
        
        # Start the scheduler
        self.scheduler.start()
        logger.info("Data generation scheduler started successfully")
        
        # Shutdown scheduler when app stops
        import atexit
        atexit.register(lambda: self.shutdown())
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown complete")
    
    def get_jobs(self):
        """Get all scheduled jobs"""
        if not self.scheduler:
            return []
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def run_job_now(self, job_id):
        """Manually trigger a job"""
        if not self.scheduler:
            raise Exception("Scheduler not initialized")
        
        job = self.scheduler.get_job(job_id)
        if not job:
            raise Exception(f"Job {job_id} not found")
        
        # Execute the job immediately
        job.func()
        return True
    
    def pause_job(self, job_id):
        """Pause a scheduled job"""
        if not self.scheduler:
            raise Exception("Scheduler not initialized")
        
        self.scheduler.pause_job(job_id)
        return True
    
    def resume_job(self, job_id):
        """Resume a paused job"""
        if not self.scheduler:
            raise Exception("Scheduler not initialized")
        
        self.scheduler.resume_job(job_id)
        return True

# Create global scheduler instance
data_scheduler = DataScheduler()