import subprocess
import sys


def _run_help(*args: str) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "src", *args, "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    return result.stdout + result.stderr


def test_fire_index_help() -> None:
    output = _run_help("index")
    assert "max_chunk_size" in output
    assert "max_chunk_size" in output


def test_fire_lists_search_dataset() -> None:
    output = _run_help("search_dataset")
    assert "dataset_path" in output
    assert "save_directory" in output
