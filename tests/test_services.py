from pytest import MonkeyPatch

from src import services
from src.models import MinimalSource, StudentSearchResults


def test_search_query_returns_model(monkeypatch: MonkeyPatch) -> None:
    source = MinimalSource(
        file_path="docs/example.md",
        first_character_index=0,
        last_character_index=10,
    )
    monkeypatch.setattr(
        services,
        "search",
        lambda query, k: [source],
    )

    result = services.search_query("Question?", 1)

    assert isinstance(result, StudentSearchResults)
    assert result.search_results[0].retrieved_sources == [source]
