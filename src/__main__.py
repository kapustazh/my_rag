from pathlib import Path
import sys
import fire

from src.ingest import ingest_chunks
from src.retrieve import build_index
from src.validators import validate_file, validate_k, validate_query
from src.validators import validate_max_chunk_size


class RAGCli:
    def index(self, *, max_chunk_size: int = 2000) -> None:
        """Ingest data/raw/ and build the index under data/processed/."""
        validate_max_chunk_size(max_chunk_size)
        chunks = ingest_chunks(max_chunk_size)
        build_index(chunks)

    def search(self, query: str, *, k: int) -> None:
        """Return the top-k sources for a single query."""
        validate_query(query)
        validate_k(k)

    def search_dataset(
        self, *, dataset_path: Path, k: int, save_directory: Path
    ) -> None:
        """Run search over a whole dataset and write a StudentSearchResults
        JSON file."""
        validate_file(dataset_path)
        validate_k(k)

    def answer(self, query: str, *, k: int) -> None:
        """Answer a single query using the retrieved context."""
        validate_query(query)
        validate_k(k)

    def answer_dataset(
        self, *, student_search_results_path: Path, save_directory: Path
    ) -> None:
        """Generate answers for a dataset, producing a
        StudentSearchResultsAndAnswer JSON file."""
        validate_file(student_search_results_path)

    def evaluate(
        self, *, student_search_results_path: Path, dataset_path: Path
    ) -> None:
        """Report your own recall@k against a ground-truth dataset,
        for your own testing."""
        validate_file(student_search_results_path)
        validate_file(dataset_path)


def main() -> None:
    try:
        fire.Fire(RAGCli)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
