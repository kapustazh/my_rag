from pathlib import Path

from src.cli import CLI


REQUIRED_COMMANDS = (
    "index",
    "search",
    "search_dataset",
    "answer",
    "answer_dataset",
    "evaluate",
)


def test_cli_exposes_required_commands() -> None:
    cli = CLI()
    for name in REQUIRED_COMMANDS:
        assert callable(getattr(cli, name))


def test_cli_stubs_do_not_raise(tmp_path: Path) -> None:
    cli = CLI()
    cli.index(max_chunk_size=2000)
    cli.search("how does moritz work?", k=5)
    cli.search_dataset(
        dataset_path=tmp_path / "dataset.json",
        k=5,
        save_directory=tmp_path / "out",
    )
    cli.answer("how does moritz work?", k=5)
    cli.answer_dataset(
        student_search_results_path=tmp_path / "results.json",
        save_directory=tmp_path / "answers",
    )
    cli.evaluate(
        student_search_results_path=tmp_path / "results.json",
        dataset_path=tmp_path / "dataset.json",
    )
