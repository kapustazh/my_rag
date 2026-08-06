from pathlib import Path
from typing import Iterator

from tqdm import tqdm

from src.chunk import chunk_python, chunk_markdown
from src.models import Chunk

_DOC_EXTENSIONS = {".md", ".py"}
_SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    ".pytest_cache",
    ".mypy_cache",
}


def _should_skip(path: Path) -> bool:
    return any(part in _SKIP_DIRS for part in path.parts)


def iter_required_files(root: Path) -> Iterator[Path]:
    seen: set[Path] = set()

    for path in root.glob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _DOC_EXTENSIONS:
            continue
        if _should_skip(path):
            continue
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"Failed to read text from {path}: {exc}") from exc


def ingest_chunks(max_chunk_size: int) -> list[Chunk]:
    root = Path("data/raw")
    if not root.is_dir():
        raise FileNotFoundError(f"Corpus directory not found: {root}")

    project_root = Path.cwd().resolve()
    chunks: list[Chunk] = []
    required_files = list(iter_required_files(root))
    for path in tqdm(required_files, desc="Ingesting files"):
        text = read_text(path)
        file_path = path.resolve().relative_to(project_root).as_posix()

        if path.suffix == ".py":
            chunk_ranges = chunk_python(text, max_chunk_size)
        else:
            chunk_ranges = chunk_markdown(text, max_chunk_size)

        for start, end in chunk_ranges:
            chunks.append(
                Chunk(
                    file_path=file_path,
                    first_character_index=start,
                    last_character_index=end,
                    text=text[start:end],
                )
            )
    return chunks
