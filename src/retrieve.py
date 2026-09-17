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
    """Tokenize text while preserving and splitting identifiers.

    Args:
        text: Text to tokenize.

    Returns:
        Lowercase lexical tokens.
    """
    tokens: list[str] = []
    for tok in _TOKEN.findall(text.lower()):
        tokens.append(tok)
        if "_" in tok:
            tokens.extend(part for part in tok.split("_") if part)
    return tokens


def _path_tokens(file_path: str) -> list[str]:
    """Extract searchable tokens from a file name and parent directory.

    Args:
        file_path: Corpus-relative source path.

    Returns:
        Tokens derived from the path.
    """
    path = Path(file_path)
    return tokenize(path.stem) + tokenize(path.parent.name)


def build_index(chunks: list[Chunk]) -> bm25s.BM25:
    """Build and persist a BM25 index for source chunks.

    Args:
        chunks: Source chunks to index.

    Returns:
        The populated BM25 retriever.

    Raises:
        ValueError: If no chunks are supplied.
    """
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
    """Load the persisted BM25 index and source metadata.

    Returns:
        The stored BM25 retriever.

    Raises:
        FileNotFoundError: If the index has not been created.
    """
    if not (INDEX_DIR / "params.index.json").is_file():
        raise FileNotFoundError(
            f"Index not found: {INDEX_DIR}. Run index first."
        )
    return bm25s.BM25.load(INDEX_DIR, load_corpus=True)


def search(query: str, k: int) -> list[MinimalSource]:
    """Retrieve the highest-ranked sources for a query.

    Args:
        query: Natural-language or identifier-based search query.
        k: Maximum number of sources to return.

    Returns:
        Ranked source locations, or an empty list for no usable tokens.
    """
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
