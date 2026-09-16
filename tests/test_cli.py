from src.__main__ import RAGCli
from pytest import raises


REQUIRED_COMMANDS = (
    "index",
    "search",
    "search_dataset",
    "answer",
    "answer_dataset",
    "evaluate",
)


def test_cli_exposes_required_commands() -> None:
    cli = RAGCli()

    for name in REQUIRED_COMMANDS:
        assert callable(getattr(cli, name))


def test_cli_rejects_fire_casted_values() -> None:
    cli = RAGCli()

    with raises(TypeError, match="query must be a string"):
        cli.search(123, k=1)  # type: ignore[arg-type]

    with raises(TypeError, match="k must be an integer"):
        cli.search("question", k="1")  # type: ignore[arg-type]

    with raises(TypeError, match="max_chunk_size must be an integer"):
        cli.index(max_chunk_size="2000")  # type: ignore[arg-type]
