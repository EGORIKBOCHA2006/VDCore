import logging
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import DownloadTaskForm
from .models import DownloadTask
from .services.kafka_producer import send_chunk_task, send_status_update
from .services.partitioner import partition_range


logger = logging.getLogger("tasks.views")

WORKERS_COUNT = 3


@login_required
def create_task(request):
    logger.warning(
        "CREATE_TASK ENTERED: method=%s path=%s user=%s",
        request.method,
        request.path,
        request.user.username,
    )

    if request.method == "POST":
        logger.warning("CREATE_TASK POST DATA: %s", request.POST)

        form = DownloadTaskForm(request.POST)

        if not form.is_valid():
            logger.error("CREATE_TASK FORM INVALID: %s", form.errors)
            return render(
                request,
                "tasks/create_task.html",
                {"form": form},
            )

        logger.warning("CREATE_TASK FORM VALID")

        start_id = form.cleaned_data["start_id"]
        end_id = form.cleaned_data["end_id"]

        task_id = str(uuid.uuid4())
        chunks = partition_range(
            start_id,
            end_id,
            WORKERS_COUNT,
        )

        logger.warning(
            "CREATE_TASK KAFKA START: task_id=%s chunks=%s",
            task_id,
            len(chunks),
        )

        try:
            send_status_update(
                task_id=task_id,
                chunk_id=None,
                status="created",
                user=request.user.username,
                start_id=start_id,
                end_id=end_id,
                chunks_count=len(chunks),
            )

            for chunk_start, chunk_end in chunks:
                chunk_id = str(uuid.uuid4())

                send_chunk_task(
                    task_id=task_id,
                    chunk_id=chunk_id,
                    range_start=chunk_start,
                    range_end=chunk_end,
                )

                send_status_update(
                    task_id=task_id,
                    chunk_id=chunk_id,
                    status="dispatched",
                    range_start=chunk_start,
                    range_end=chunk_end,
                )

        except Exception:
            logger.exception(
                "CREATE_TASK KAFKA ERROR: task_id=%s",
                task_id,
            )
            messages.error(
                request,
                "Ошибка отправки задачи в Kafka",
            )
            return redirect("create_task")

        logger.warning(
            "CREATE_TASK SUCCESS: task_id=%s",
            task_id,
        )

        messages.success(
            request,
            f"Задача {task_id} создана: "
            f"{len(chunks)} чанков отправлено в Kafka",
        )

        return redirect("task_list")

    logger.warning("CREATE_TASK GET")

    form = DownloadTaskForm()

    return render(
        request,
        "tasks/create_task.html",
        {"form": form},
    )


@login_required
def task_list(request):
    logger.warning(
        "TASK_LIST: user=%s",
        request.user.username,
    )

    tasks = (
        DownloadTask.objects
        .filter(username=request.user.username)
        .prefetch_related("chunks")
    )

    return render(
        request,
        "tasks/task_list.html",
        {"tasks": tasks},
    )