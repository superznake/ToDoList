from celery import shared_task
from django.utils.timezone import now
from .models import Task
from .signals import deadline_reached


@shared_task
def send_deadline_notifications():
    today = now().date()
    tasks = Task.objects.filter(deadline=today)
    for task in tasks:
        deadline_reached.send(sender=Task, task=task)
