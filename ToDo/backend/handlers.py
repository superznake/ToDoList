from django.dispatch import receiver
from .signals import deadline_reached


@receiver(deadline_reached)
def log_deadline(sender, task, **kwargs):
    print(f"Лог: задача '{task.name}' требует внимания")
