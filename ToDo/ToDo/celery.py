from celery import Celery
from celery.schedules import crontab

app = Celery('ToDo')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-deadline-notifications-every-day': {
        'task': 'backend.tasks.send_deadline_notifications',
        'schedule': crontab(hour=9, minute=0),  # запускать каждый день в 9:00
    },
}
