from django.contrib.auth.models import User
from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name


class Task(models.Model):
    name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='tasks')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    deadline = models.DateField(null=True, blank=True)
    done = models.BooleanField(default=False)

    def __str__(self):
        return self.name
