import json
import uuid
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
from django.conf import settings


logger = logging.getLogger("kafka_utils")
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    log_dir = Path(settings.BASE_DIR) / "logs"
    log_dir.mkdir(exist_ok=True)

    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "kafka.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    kafka_lib_logger = logging.getLogger("kafka")
    kafka_lib_logger.setLevel(logging.DEBUG)
    kafka_lib_logger.addHandler(file_handler)


_producer = None


def get_producer() -> KafkaProducer:
    global _producer
    if _producer is None:
        logger.info(
            "Инициализация KafkaProducer | bootstrap_servers=%s | sasl_username=%s | security_protocol=SASL_PLAINTEXT",
            settings.KAFKA_BOOTSTRAP_SERVERS,
            settings.KAFKA_SASL_USERNAME,
        )
        _producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
            security_protocol="SASL_PLAINTEXT",
            sasl_mechanism="PLAIN",
            sasl_plain_username=settings.KAFKA_SASL_USERNAME,
            sasl_plain_password=settings.KAFKA_SASL_PASSWORD,
            request_timeout_ms=30000,
            max_block_ms=30000,
            retries=5,
        )
        logger.info("KafkaProducer успешно инициализирован")
    return _producer


def send_message(topic: str, message: dict) -> None:
    producer = get_producer()
    payload_str = json.dumps(message, ensure_ascii=False)
    payload_size = len(payload_str.encode("utf-8"))

    logger.debug(
        "Попытка отправки | topic=%s | size=%d bytes | payload=%s",
        topic, payload_size, payload_str,
    )

    try:
        future = producer.send(topic, value=message)
        result = future.get(timeout=30)
        logger.info(
            "Сообщение доставлено | topic=%s | partition=%d | offset=%d | "
            "timestamp=%s | size=%d bytes | payload=%s",
            result.topic,
            result.partition,
            result.offset,
            result.timestamp,
            payload_size,
            payload_str,
        )
    except KafkaError as e:
        logger.error(
            "Ошибка отправки | topic=%s | size=%d bytes | payload=%s | error=%s",
            topic, payload_size, payload_str, e,
            exc_info=True,
        )
        raise RuntimeError(f"Не удалось отправить сообщение в топик {topic}: {e}")


def send_chunk_task(task_id: str, chunk_id: str, range_start: int, range_end: int) -> None:
    logger.debug(
        "send_chunk_task вызван | task_id=%s | chunk_id=%s | range=[%d, %d]",
        task_id, chunk_id, range_start, range_end,
    )
    send_message(settings.KAFKA_TASKS_TOPIC, {
        "task_id": task_id,
        "chunk_id": chunk_id,
        "range_start": range_start,
        "range_end": range_end,
    })


def send_status_update(task_id: str, chunk_id: Optional[str], status: str, **extra) -> None:
    logger.debug(
        "send_status_update вызван | task_id=%s | chunk_id=%s | status=%s | extra=%s",
        task_id, chunk_id, status, extra,
    )
    payload = {
        "task_id": task_id,
        "chunk_id": chunk_id,
        "status": status,
    }
    payload.update(extra)
    send_message(settings.KAFKA_STATUS_TOPIC, payload)