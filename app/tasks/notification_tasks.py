from app.core.celery_worker import celery_app


@celery_app.task
def send_sms_task(phone: str, message: str):
    print(f"Sending SMS to {phone}: {message}")
    # Later integrate real SMS API
