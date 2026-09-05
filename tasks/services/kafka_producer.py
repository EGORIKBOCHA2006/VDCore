import json
import uuid
from typing import Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
from django.conf import settings

_producer = None


def get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        print("KAFKA CONNECT PARAMS:", settings.KAFKA_BOOTSTRAP_SERVERS, settings.KAFKA_SASL_USERNAME)
        _producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            security_protocol="SASL_PLAINTEXT",
            sasl_mechanism="PLAIN",
            sasl_plain_username=settings.KAFKA_SASL_USERNAME,
            sasl_plain_password=settings.KAFKA_SASL_PASSWORD,
            request_timeout_ms=5000,
            max_block_ms=5000,
        )
    return _producer


def send_message(topic: str, message: dict) -> None:
    producer = get_producer()
    try:
        future = producer.send(topic, value=message)
        future.get(timeout=5)
    except KafkaError as e:
        raise RuntimeError(f"Не удалось отправить сообщение в топик {topic}: {e}")


def send_chunk_task(task_id: str, chunk_id: str, range_start: int, range_end: int) -> None:
    send_message(settings.KAFKA_TASKS_TOPIC, {
        "task_id": task_id,
        "chunk_id": chunk_id,
        "range_start": range_start,
        "range_end": range_end,
    })


def send_status_update(task_id: str, chunk_id: Optional[str], status: str, **extra) -> None:
    payload = {
        "task_id": task_id,
        "chunk_id": chunk_id,
        "status": status,
    }
    payload.update(extra)
    send_message(settings.KAFKA_STATUS_TOPIC, payload)