from pydantic import ValidationError
from pytest import MonkeyPatch, raises

from src import api
from src.models import (
    MinimalAnswer,
    MinimalSearchResults,
    MinimalSource,
    StudentSearchResults,
    StudentSearchResultsAndAnswer,
)


source = MinimalSource(
    file_path="docs/example.md",
    first_character_index=0,
    last_character_index=10,
)


def test_search(monkeypatch: MonkeyPatch) -> None:
    def fake_search(query: str, k: int) -> StudentSearchResults:
        return StudentSearchResults(
            k=k,
            search_results=[
                MinimalSearchResults(
                    question_id="",
                    question=query,
                    retrieved_sources=[source],
                )
            ],
        )

    monkeypatch.setattr(api, "search_query", fake_search)

    response = api.search(api.QueryRequest(query="Question?", k=1))

    assert response.search_results[0].question == "Question?"


def test_answer(monkeypatch: MonkeyPatch) -> None:
    def fake_answer(
        query: str,
        k: int,
        generator: object,
    ) -> StudentSearchResultsAndAnswer:
        return StudentSearchResultsAndAnswer(
            k=k,
            search_results=[
                MinimalAnswer(
                    question_id="",
                    question=query,
                    retrieved_sources=[source],
                    answer="Answer.",
                )
            ],
        )

    monkeypatch.setattr(api, "answer_query", fake_answer)

    response = api.answer(api.QueryRequest(query="Question?", k=1))

    assert response.search_results[0].answer == "Answer."


def test_request_validation() -> None:
    with raises(ValidationError):
        api.QueryRequest(query="   ", k=0)
