from src.__main__ import RAGCli


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
