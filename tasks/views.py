import uuid
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import DownloadTask
from .forms import DownloadTaskForm
from .services.partitioner import partition_range
from .services.kafka_producer import send_chunk_task, send_status_update

WORKERS_COUNT = 3


@login_required
def create_task(request):
    if request.method == "POST":
        form = DownloadTaskForm(request.POST)
        if form.is_valid():
            start_id = form.cleaned_data["start_id"]
            end_id = form.cleaned_data["end_id"]

            task_id = str(uuid.uuid4())
            chunks = partition_range(start_id, end_id, WORKERS_COUNT)

            try:
                send_status_update(
                    task_id=task_id, chunk_id=None, status="created",
                    user=request.user.username, start_id=start_id, end_id=end_id,
                    chunks_count=len(chunks),
                )
                for chunk_start, chunk_end in chunks:
                    chunk_id = str(uuid.uuid4())
                    send_chunk_task(task_id, chunk_id, chunk_start, chunk_end)
                    send_status_update(
                        task_id=task_id, chunk_id=chunk_id, status="dispatched",
                        range_start=chunk_start, range_end=chunk_end,
                    )
            except RuntimeError as e:
                messages.error(request, str(e))
                return redirect("create_task")

            messages.success(request, f"Задача {task_id} создана: {len(chunks)} чанков отправлено в Kafka")
            return redirect("task_list")
    else:
        form = DownloadTaskForm()
    return render(request, "tasks/create_task.html", {"form": form})


@login_required
def task_list(request):
    tasks = DownloadTask.objects.filter(username=request.user.username).prefetch_related("chunks")
    return render(request, "tasks/task_list.html", {"tasks": tasks})