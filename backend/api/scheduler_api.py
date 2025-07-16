"""API endpoints for scheduler management"""

from flask import Blueprint, jsonify, request
from scheduler.scheduler import data_scheduler
from scheduler.config import DAILY_JOBS, ENABLE_SCHEDULER
import logging
import os

logger = logging.getLogger(__name__)

scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/api/scheduler')

@scheduler_bp.route('/status', methods=['GET'])
def get_scheduler_status():
    """Get scheduler status and configuration"""
    try:
        return jsonify({
            "enabled": ENABLE_SCHEDULER,
            "running": data_scheduler.scheduler is not None and data_scheduler.scheduler.running,
            "jobs_count": len(DAILY_JOBS),
            "timezone": "UTC",
            "jobs": data_scheduler.get_jobs()
        })
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        return jsonify({"error": str(e)}), 500

@scheduler_bp.route('/jobs', methods=['GET'])
def get_all_jobs():
    """Get all scheduled jobs with their configurations"""
    try:
        scheduled_jobs = data_scheduler.get_jobs()
        job_configs = []
        
        for job_name, config in DAILY_JOBS.items():
            job_info = {
                "id": job_name,
                "description": config['description'],
                "schedule": f"{config['hour']:02d}:{config['minute']:02d} UTC daily",
                "enabled": any(j['id'] == job_name for j in scheduled_jobs)
            }
            
            # Find next run time
            for sj in scheduled_jobs:
                if sj['id'] == job_name:
                    job_info['next_run'] = sj['next_run']
                    break
            
            job_configs.append(job_info)
        
        return jsonify({
            "jobs": job_configs,
            "total": len(job_configs)
        })
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        return jsonify({"error": str(e)}), 500

@scheduler_bp.route('/jobs/<job_id>/run', methods=['POST'])
def run_job_now(job_id):
    """Manually trigger a specific job"""
    try:
        if not ENABLE_SCHEDULER:
            return jsonify({"error": "Scheduler is disabled"}), 400
        
        if job_id not in DAILY_JOBS:
            return jsonify({"error": f"Job {job_id} not found"}), 404
        
        # Run the job
        data_scheduler.run_job_now(job_id)
        
        return jsonify({
            "success": True,
            "message": f"Job {job_id} triggered successfully",
            "job": job_id,
            "description": DAILY_JOBS[job_id]['description']
        })
    except Exception as e:
        logger.error(f"Error running job {job_id}: {e}")
        return jsonify({"error": str(e)}), 500

@scheduler_bp.route('/jobs/<job_id>/pause', methods=['POST'])
def pause_job(job_id):
    """Pause a scheduled job"""
    try:
        if not ENABLE_SCHEDULER:
            return jsonify({"error": "Scheduler is disabled"}), 400
        
        data_scheduler.pause_job(job_id)
        
        return jsonify({
            "success": True,
            "message": f"Job {job_id} paused",
            "job": job_id
        })
    except Exception as e:
        logger.error(f"Error pausing job {job_id}: {e}")
        return jsonify({"error": str(e)}), 500

@scheduler_bp.route('/jobs/<job_id>/resume', methods=['POST'])
def resume_job(job_id):
    """Resume a paused job"""
    try:
        if not ENABLE_SCHEDULER:
            return jsonify({"error": "Scheduler is disabled"}), 400
        
        data_scheduler.resume_job(job_id)
        
        return jsonify({
            "success": True,
            "message": f"Job {job_id} resumed",
            "job": job_id
        })
    except Exception as e:
        logger.error(f"Error resuming job {job_id}: {e}")
        return jsonify({"error": str(e)}), 500

@scheduler_bp.route('/run-all', methods=['POST'])
def run_all_jobs():
    """Run all jobs immediately (useful for testing)"""
    try:
        if not ENABLE_SCHEDULER:
            return jsonify({"error": "Scheduler is disabled"}), 400
        
        results = []
        for job_id in DAILY_JOBS.keys():
            try:
                data_scheduler.run_job_now(job_id)
                results.append({
                    "job": job_id,
                    "status": "success",
                    "description": DAILY_JOBS[job_id]['description']
                })
            except Exception as e:
                results.append({
                    "job": job_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r['status'] == 'success')
        
        return jsonify({
            "success": success_count == len(results),
            "message": f"{success_count}/{len(results)} jobs executed successfully",
            "results": results
        })
    except Exception as e:
        logger.error(f"Error running all jobs: {e}")
        return jsonify({"error": str(e)}), 500

@scheduler_bp.route('/config', methods=['GET'])
def get_scheduler_config():
    """Get scheduler configuration"""
    try:
        return jsonify({
            "enabled": ENABLE_SCHEDULER,
            "timezone": "UTC",
            "daily_jobs": [
                {
                    "id": job_id,
                    "description": config['description'],
                    "hour": config['hour'],
                    "minute": config['minute']
                }
                for job_id, config in DAILY_JOBS.items()
            ],
            "environment": {
                "RAILWAY_ENVIRONMENT": os.getenv('RAILWAY_ENVIRONMENT', 'development'),
                "TZ": os.getenv('TZ', 'UTC'),
                "ENABLE_SCHEDULER": os.getenv('ENABLE_SCHEDULER', 'true')
            }
        })
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({"error": str(e)}), 500