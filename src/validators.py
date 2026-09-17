from pathlib import Path
import json


def validate_string(value: object, name: str) -> str:
    """Validate and return a string CLI argument.

    Args:
        value: Value to validate.
        name: Argument name used in error messages.

    Returns:
        The validated string.

    Raises:
        TypeError: If the value is not a string.
    """
    if not isinstance(value, str):
        raise TypeError(
            f"{name} must be a string, got {type(value).__name__}."
        )
    return value


def validate_integer(value: object, name: str) -> int:
    """Validate and return an integer CLI argument.

    Args:
        value: Value to validate.
        name: Argument name used in error messages.

    Returns:
        The validated integer.

    Raises:
        TypeError: If the value is not an integer or is a boolean.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"{name} must be an integer, got {type(value).__name__}."
        )
    return value


def validate_file(path: Path) -> None:
    """Validate that a path identifies a file.

    Args:
        path: File path to validate.

    Raises:
        FileNotFoundError: If the path does not identify a file.
    """
    if not Path(path).is_file():
        raise FileNotFoundError(f"File not found: {path}")


def validate_k(k: object) -> None:
    """Validate the requested number of search results.

    Args:
        k: Requested result count.

    Raises:
        TypeError: If the value is not an integer.
        ValueError: If the value is less than one.
    """
    k = validate_integer(k, "k")
    if k < 1:
        raise ValueError(f"Invalid k: {k}. Must be greater than 0.")


def validate_query(query: object) -> None:
    """Validate a non-empty search query.

    Args:
        query: Query value to validate.

    Raises:
        TypeError: If the query is not a string.
        ValueError: If the query is empty or contains only whitespace.
    """
    query = validate_string(query, "query")
    if not query.strip() or not query:
        raise ValueError("Query cannot be empty.")


def validate_json(path: Path) -> None:
    """Validate that a path exists and contains a JSON document.

    Args:
        path: JSON file path to validate.

    Raises:
        FileNotFoundError: If the path does not identify a file.
        ValueError: If the file does not contain valid JSON.
    """
    validate_file(path)
    try:
        with open(path, "r") as f:
            json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {path}: {exc}") from exc


def validate_max_chunk_size(max_chunk_size: object) -> None:
    """Validate the configured maximum chunk size.

    Args:
        max_chunk_size: Maximum chunk size to validate.

    Raises:
        TypeError: If the value is not an integer.
        ValueError: If the value is outside the range 1 through 2,000.
    """
    max_chunk_size = validate_integer(max_chunk_size, "max_chunk_size")
    if not 1 <= max_chunk_size <= 2000:
        raise ValueError(
            f"Invalid max_chunk_size: {max_chunk_size}. "
            + "Must be between 1 and 2000."
        )
