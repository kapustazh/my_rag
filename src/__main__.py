from pathlib import Path
import sys
import fire
from tqdm import tqdm

from src.evaluate import recall_at_k
from src.generate import QwenGenerator, generate_answer
from src.ingest import ingest_chunks
from src.models import (
    MinimalAnswer,
    MinimalSearchResults,
    RagDataset,
    StudentSearchResults,
    StudentSearchResultsAndAnswer,
)
from src.retrieve import build_index
from src.retrieve import search as retrieve_search
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
        print(
            StudentSearchResults(
                k=k,
                search_results=[
                    MinimalSearchResults(
                        question_id="",
                        question=query,
                        retrieved_sources=retrieve_search(query, k),
                    )
                ],
            ).model_dump_json(indent=2)
        )

    def search_dataset(
        self, *, dataset_path: str, k: int, save_directory: str
    ) -> None:
        """Run search over a whole dataset and write a StudentSearchResults
        JSON file."""
        dataset_file = Path(dataset_path)
        output_directory = Path(save_directory)
        validate_file(dataset_file)
        validate_k(k)
        dataset = RagDataset.model_validate_json(dataset_file.read_text())
        results = StudentSearchResults(
            k=k,
            search_results=[
                MinimalSearchResults(
                    question_id=question.question_id,
                    question=question.question,
                    retrieved_sources=retrieve_search(question.question, k),
                )
                for question in tqdm(
                    dataset.rag_questions, desc="Searching"
                )
            ],
        )
        output_directory.mkdir(parents=True, exist_ok=True)
        out = output_directory / dataset_file.name
        out.write_text(results.model_dump_json(indent=2))
        print(f"Wrote {out}")

    def answer(self, query: str, *, k: int) -> None:
        """Answer a single query using the retrieved context."""
        validate_query(query)
        validate_k(k)
        sources = retrieve_search(query, k)
        answer = generate_answer(query, sources, QwenGenerator())
        result = StudentSearchResultsAndAnswer(
            k=k,
            search_results=[
                MinimalAnswer(
                    question_id="",
                    question=query,
                    retrieved_sources=sources,
                    answer=answer,
                )
            ],
        )
        print(result.model_dump_json(indent=2))

    def answer_dataset(
        self, *, student_search_results_path: str, save_directory: str
    ) -> None:
        """Generate answers for a dataset, producing a
        StudentSearchResultsAndAnswer JSON file."""
        results_file = Path(student_search_results_path)
        output_directory = Path(save_directory)
        validate_file(results_file)
        results = StudentSearchResults.model_validate_json(
            results_file.read_text(encoding="utf-8")
        )
        generator = QwenGenerator()
        answered = StudentSearchResultsAndAnswer(
            k=results.k,
            search_results=[
                MinimalAnswer(
                    question_id=item.question_id,
                    question=item.question,
                    retrieved_sources=item.retrieved_sources,
                    answer=generate_answer(
                        item.question,
                        item.retrieved_sources,
                        generator,
                    ),
                )
                for item in tqdm(results.search_results, desc="Generating")
            ],
        )
        output_directory.mkdir(parents=True, exist_ok=True)
        output_path = output_directory / results_file.name
        output_path.write_text(
            answered.model_dump_json(indent=2),
            encoding="utf-8",
        )
        print(f"Wrote {output_path}")

    def evaluate(
        self, *, student_search_results_path: str, dataset_path: str
    ) -> None:
        """Report your own recall@k against a ground-truth dataset,
        for your own testing."""
        results_file = Path(student_search_results_path)
        dataset_file = Path(dataset_path)
        validate_file(results_file)
        validate_file(dataset_file)
        results = StudentSearchResults.model_validate_json(
            results_file.read_text()
        )
        dataset = RagDataset.model_validate_json(dataset_file.read_text())
        score = recall_at_k(results, dataset)
        print(f"recall@{results.k}: {score:.4f}")


def main() -> None:
    try:
        fire.Fire(RAGCli)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
