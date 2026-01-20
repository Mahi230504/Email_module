"""
Celery application configuration.
"""

import os
import sys

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery import Celery
from app.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "email_module",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks.email_tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Task time limits
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    
    # Task retry
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Result backend
    result_expires=3600,  # 1 hour
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "renew-subscriptions": {
            "task": "tasks.email_tasks.renew_expiring_subscriptions",
            "schedule": 3600.0,  # Every hour
        },
        "background-sync": {
            "task": "tasks.email_tasks.background_email_sync",
            "schedule": float(settings.background_sync_interval),  # Default: 120 seconds
        },
    },
)


if __name__ == "__main__":
    celery_app.start()
