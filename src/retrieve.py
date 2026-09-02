import re
import bm25s
from pathlib import Path

from src.models import Chunk, MinimalSource

_TOKEN = re.compile(r"[a-z0-9_]+")
_QUESTION_STOPWORDS = frozenset(
    {
        "what",
        "is",
        "are",
        "how",
        "does",
        "do",
        "why",
        "when",
        "where",
        "which",
        "who",
        "the",
        "a",
        "an",
        "in",
        "of",
        "for",
        "to",
        "and",
        "explain",
        "describe",
        "tell",
        "me",
        "about",
    }
)
INDEX_DIR = Path("data/processed/lexical")


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    for tok in _TOKEN.findall(text.lower()):
        tokens.append(tok)
        if "_" in tok:
            tokens.extend(part for part in tok.split("_") if part)
    return tokens


def _path_tokens(file_path: str) -> list[str]:
    path = Path(file_path)
    return tokenize(path.stem) + tokenize(path.parent.name)


def build_index(chunks: list[Chunk]) -> bm25s.BM25:
    if not chunks:
        raise ValueError("No chunks to index")
    tokenized_chunks = [
        _path_tokens(chunk.file_path) * 3 + tokenize(chunk.text)
        for chunk in chunks
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
    keywords = [t for t in tokens if t not in _QUESTION_STOPWORDS]
    tokens = keywords or tokens
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
