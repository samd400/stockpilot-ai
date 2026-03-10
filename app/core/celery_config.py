from celery import Celery
from celery.schedules import crontab
import os

# Create Celery app
celery_app = Celery(
    "stockpilot",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
)

# Celery Beat Schedule
celery_app.conf.beat_schedule = {
    # Existing tasks
    "check-subscription-expiry": {
        "task": "app.tasks.subscription_tasks.check_subscription_expiry",
        "schedule": crontab(hour=0, minute=0),
    },
    "send-subscription-reminders": {
        "task": "app.tasks.subscription_tasks.send_subscription_expiry_reminder",
        "schedule": crontab(hour=9, minute=0),
    },
    "calculate-revenue-metrics": {
        "task": "app.tasks.subscription_tasks.calculate_revenue_metrics",
        "schedule": crontab(hour=1, minute=0),
    },
    "send-sms-notifications": {
        "task": "app.tasks.notification_tasks.send_pending_sms",
        "schedule": crontab(minute="*/5"),
    },
    # Agent tasks
    "agent-stock-monitor": {
        "task": "app.tasks.agent_tasks.run_stock_agent",
        "schedule": crontab(hour="*/4"),  # Every 4 hours
    },
    "agent-profit-analysis": {
        "task": "app.tasks.agent_tasks.run_profit_agent",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    "agent-pricing-suggestions": {
        "task": "app.tasks.agent_tasks.run_pricing_agent",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    "agent-subscription-check": {
        "task": "app.tasks.agent_tasks.run_subscription_agent",
        "schedule": crontab(hour=0, minute=30),  # Daily at 00:30
    },
    "agent-storefront-sync": {
        "task": "app.tasks.agent_tasks.run_sync_agent",
        "schedule": crontab(hour="*/6"),  # Every 6 hours
    },
    # Procurement agent
    "agent-procurement": {
        "task": "app.tasks.procurement_tasks.run_procurement_for_all_tenants",
        "schedule": crontab(hour="*/8"),  # Every 8 hours
    },
}

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
