from src.generate import QwenGenerator, generate_answer
from src.models import (
    MinimalAnswer,
    MinimalSearchResults,
    StudentSearchResults,
    StudentSearchResultsAndAnswer,
)
from src.retrieve import search
from src.validators import validate_k, validate_query


def search_query(query: str, k: int) -> StudentSearchResults:
    """Return the top-k sources for a single query."""
    validate_query(query)
    validate_k(k)
    return StudentSearchResults(
        k=k,
        search_results=[
            MinimalSearchResults(
                question_id="",
                question=query,
                retrieved_sources=search(query, k),
            )
        ],
    )


def answer_query(
    query: str,
    k: int,
    generator: QwenGenerator,
) -> StudentSearchResultsAndAnswer:
    search_result = search_query(query, k)
    result = search_result.search_results[0]
    return StudentSearchResultsAndAnswer(
        k=k,
        search_results=[
            MinimalAnswer(
                **result.model_dump(),
                answer=generate_answer(
                    query,
                    result.retrieved_sources,
                    generator,
                ),
            )
        ],
    )
