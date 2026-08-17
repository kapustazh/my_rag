from pathlib import Path

from tqdm import tqdm

from src.chunk import chunk_python, chunk_markdown
from src.models import Chunk

_RAW_ROOT = Path("data/raw/vllm-0.10.1")
_EXTENSIONS = {".md", ".py"}
_SKIP_DIRS = {
    ".git",
    ".github",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    ".tox",
    ".eggs",
    "eggs",
    "__pycache__",
    "dist",
    "build",
}


def ingest_chunks(max_chunk_size: int) -> list[Chunk]:
    root = _RAW_ROOT
    if not root.is_dir():
        raise FileNotFoundError(f"Corpus directory not found: {root}")

    project_root = Path.cwd().resolve()
    chunks: list[Chunk] = []
    paths = (
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in _EXTENSIONS
        and not any(
            part in _SKIP_DIRS or part.endswith(".egg-info")
            for part in path.parts
        )
    )
    for path in tqdm(paths, desc="Ingesting files"):
        text = path.read_text(encoding="utf-8")
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
