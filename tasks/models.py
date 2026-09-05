import uuid
from django.db import models


class DownloadTask(models.Model):
    STATUS_CREATED = "created"
    STATUS_DISPATCHED = "dispatched"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_DONE = "done"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_CREATED, "Создана"),
        (STATUS_DISPATCHED, "Отправлена в Kafka"),
        (STATUS_IN_PROGRESS, "В процессе"),
        (STATUS_DONE, "Завершена"),
        (STATUS_FAILED, "Ошибка"),
    ]

    task_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150)
    start_id = models.PositiveIntegerField()
    end_id = models.PositiveIntegerField()
    chunks_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_CREATED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Task {self.task_id} [{self.start_id}-{self.end_id}] {self.status}"


class TaskChunk(models.Model):
    STATUS_DISPATCHED = "dispatched"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_DONE = "done"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_DISPATCHED, "Отправлен"),
        (STATUS_IN_PROGRESS, "В процессе"),
        (STATUS_DONE, "Завершён"),
        (STATUS_FAILED, "Ошибка"),
    ]

    chunk_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(DownloadTask, on_delete=models.CASCADE, related_name="chunks", to_field="task_id")
    range_start = models.PositiveIntegerField()
    range_end = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DISPATCHED)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["range_start"]

    def __str__(self):
        return f"Chunk {self.chunk_id} [{self.range_start}-{self.range_end}] {self.status}"