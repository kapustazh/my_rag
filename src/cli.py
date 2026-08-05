from pathlib import Path


class CLI:
    def index(self, *, max_chunk_size: int = 2000) -> None:
        """Ingest data/raw/ and build the index under data/processed/."""
        pass

    def search(self, query: str, *, k: int) -> None:
        """Return the top-k sources for a single query."""
        pass

    def search_dataset(
        self, *, dataset_path: Path, k: int, save_directory: Path
    ) -> None:
        """Run search over a whole dataset and write a StudentSearchResults
        JSON file."""
        pass

    def answer(self, query: str, *, k: int) -> None:
        """Answer a single query using the retrieved context."""
        pass

    def answer_dataset(
        self, *, student_search_results_path: Path, save_directory: Path
    ) -> None:
        """Generate answers for a dataset, producing a
        StudentSearchResultsAndAnswer JSON file."""
        pass

    def evaluate(
        self, *, student_search_results_path: Path, dataset_path: Path
    ) -> None:
        """Report your own recall@k against a ground-truth dataset,
        for your own testing."""
        pass
