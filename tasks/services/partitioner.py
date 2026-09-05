def partition_range(start_id: int, end_id: int, workers_count: int) -> list[tuple[int, int]]:
    if workers_count <= 0:
        raise ValueError("Количество воркеров должно быть больше нуля")

    total = end_id - start_id + 1
    if total < workers_count:
        workers_count = total

    base_chunk = total // workers_count
    remainder = total % workers_count

    chunks = []
    current = start_id
    for i in range(workers_count):
        size = base_chunk + (1 if i < remainder else 0)
        chunk_end = current + size - 1
        chunks.append((current, chunk_end))
        current = chunk_end + 1
    return chunks