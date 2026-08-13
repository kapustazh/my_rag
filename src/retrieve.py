import re
from pathlib import Path

import bm25s

from src.models import Chunk, MinimalSource

_FILE_PATH_TOKEN = re.compile(r"[a-z0-9_\.]+")
INDEX_DIR = Path("data/processed/lexical")


def tokenize(text: str) -> list[str]:
    return _FILE_PATH_TOKEN.findall(text.lower())


def build_index(chunks: list[Chunk]) -> bm25s.BM25:
    if not chunks:
        raise ValueError("No chunks to index")
    tokenized_chunks = [
        tokenize(f"{chunk.file_path} {chunk.text}") for chunk in chunks
    ]
    retriever = bm25s.BM25()
    retriever.index(tokenized_chunks, show_progress=True)  # tqdm progress bar
    sources = [
        {
            "file_path": chunk.file_path,
            "first_character_index": chunk.first_character_index,
            "last_character_index": chunk.last_character_index,
        }
        for chunk in chunks
    ]
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    retriever.save(INDEX_DIR, corpus=sources)
    return retriever


def load_index() -> bm25s.BM25:
    if not (INDEX_DIR / "params.index.json").is_file():
        raise FileNotFoundError(
            f"Index not found: {INDEX_DIR}. Run index first."
        )
    # TODO: Reloads per call; add cache when search_dataset hits disk twice
    return bm25s.BM25.load(INDEX_DIR, load_corpus=True)


def search(query: str, k: int) -> list[MinimalSource]:
    tokens = tokenize(query)
    # print(f"tokens: {tokens}")
    if not tokens:
        return []
    retriever = load_index()
    sources = retriever.corpus or []
    if not sources:
        return []
    results = retriever.retrieve(
        [tokens],
        corpus=sources,
        k=min(k, len(sources)),
        show_progress=False,
    )
    return [MinimalSource.model_validate(doc) for doc in results.documents[0]]


if __name__ == "__main__":
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
    build_index(chunks)
    hits = search("load_lora_adapter endpoint", k=1)
    assert hits[0].file_path == "docs/lora.md", hits
    print(hits[0])
