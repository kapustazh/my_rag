from pathlib import Path
import json


def validate_file(path: Path) -> None:
    if not Path(path).is_file():
        raise FileNotFoundError(f"File not found: {path}")


def validate_k(k: int) -> None:
    if k < 1:
        raise ValueError(f"Invalid k: {k}. Must be greater than 0.")


def validate_query(query: str) -> None:
    if not query.strip() or not query:
        raise ValueError("Query cannot be empty.")


def validate_json(path: Path) -> None:
    validate_file(path)
    try:
        with open(path, "r") as f:
            json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {path}: {exc}") from exc


def validate_max_chunk_size(max_chunk_size: int) -> None:
    if not 1 <= max_chunk_size <= 2000:
        raise ValueError(
            f"Invalid max_chunk_size: {max_chunk_size}. "
            + "Must be between 1 and 2000."
        )
