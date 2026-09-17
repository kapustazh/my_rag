from pathlib import Path

from pytest import MonkeyPatch

from src import retrieve
from src.chunk import chunk_python
from src.models import Chunk


def test_chunk_python_keeps_function() -> None:
    code = "import os\n\ndef f():\n    return 1\n\nprint(f())\n"

    ranges = chunk_python(code, 2000)

    assert any("def f" in code[start:end] for start, end in ranges)


def test_chunk_python_keeps_all_meaningful_text() -> None:
    code = (
        "GLOBAL = 1\n\n"
        "def first():\n"
        "    return GLOBAL\n\n"
        "# Keep this comment.\n"
        "BETWEEN = 2\n\n"
        "@decorator\n"
        "def second():\n"
        "    return BETWEEN\n"
    )

    ranges = chunk_python(code, 2000)
    covered = {
        index
        for start, end in ranges
        for index in range(start, end)
    }

    assert all(
        char.isspace() or index in covered
        for index, char in enumerate(code)
    )
    assert any("@decorator" in code[start:end] for start, end in ranges)


def test_search_returns_matching_source(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(retrieve, "INDEX_DIR", tmp_path / "index")
    lora = "load_lora_adapter endpoint"
    other = "unrelated python"
    chunks = [
        Chunk(
            file_path="docs/lora.md",
            first_character_index=0,
            last_character_index=len(lora),
            text=lora,
        ),
        Chunk(
            file_path="vllm/other.py",
            first_character_index=0,
            last_character_index=len(other),
            text=other,
        ),
    ]

    retrieve.build_index(chunks)
    hits = retrieve.search("load_lora_adapter endpoint", k=1)

    assert hits[0].file_path == "docs/lora.md"
