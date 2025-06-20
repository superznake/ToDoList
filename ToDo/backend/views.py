from rest_framework import viewsets, permissions
from .models import Task, Tag
from .serializers import TaskSerializer, TagSerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Возвращаем задачи только текущего пользователя
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # При создании задачи автоматически ставим текущего пользователя
        serializer.save(user=self.request.user)
