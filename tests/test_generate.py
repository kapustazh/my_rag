from pathlib import Path
from types import SimpleNamespace
from typing import Any

from src.generate import (
    QwenGenerator,
    build_prompt_to_answer,
    generate_answer,
    read_source_text,
)
from src.models import MinimalSource


def make_source(tmp_path: Path) -> MinimalSource:
    path = tmp_path / "docs" / "example.md"
    path.parent.mkdir()
    content = "prefix\nThe answer is here.\nsuffix\n"
    path.write_text(content, encoding="utf-8")
    start = content.index("The answer")
    return MinimalSource(
        file_path="docs/example.md",
        first_character_index=start,
        last_character_index=start + len("The answer is here."),
    )


def test_prompt_uses_exact_source_span(tmp_path: Path) -> None:
    source = make_source(tmp_path)

    assert read_source_text(source, tmp_path) == "The answer is here."
    prompt = build_prompt_to_answer(
        "What is the answer?", [source], tmp_path
    )

    assert "What is the answer?" in prompt
    assert "The answer is here." in prompt
    assert "docs/example.md" in prompt


def test_prompt_handles_no_sources(tmp_path: Path) -> None:
    prompt = build_prompt_to_answer("Unknown?", [], tmp_path)

    assert "(No source was retrieved.)" in prompt


def test_generate_answer_uses_built_prompt(tmp_path: Path) -> None:
    source = make_source(tmp_path)
    generator = QwenGenerator()
    seen: list[str] = []

    def answer(prompt: str) -> str:
        seen.append(prompt)
        return "Grounded answer"

    generator.answer = answer  # type: ignore[method-assign]

    result = generate_answer(
        "What is the answer?", [source], generator, tmp_path
    )

    assert result == "Grounded answer"
    assert "The answer is here." in seen[0]


class FakeInputs(dict[str, Any]):
    def to(self, device: str) -> "FakeInputs":
        return self


class FakeTokenizer:
    def __init__(self) -> None:
        self.template_options: dict[str, Any] = {}
        self.decoded_tokens: list[int] = []

    def apply_chat_template(
        self,
        messages: list[dict[str, str]],
        **options: Any,
    ) -> FakeInputs:
        self.template_options = options
        return FakeInputs(
            input_ids=SimpleNamespace(shape=(1, 4)),
        )

    def decode(
        self,
        tokens: list[int],
        skip_special_tokens: bool,
    ) -> str:
        self.decoded_tokens = tokens
        return "Generated answer"


class FakeModel:
    device = "cpu"
    config = SimpleNamespace(max_position_embeddings=100)

    def __init__(self) -> None:
        self.generation_options: dict[str, Any] = {}

    def generate(self, **options: Any) -> list[list[int]]:
        self.generation_options = options
        return [[1, 2, 3, 4, 9, 10]]


def test_generator_keeps_input_inside_token_budget() -> None:
    tokenizer = FakeTokenizer()
    model = FakeModel()
    generator = QwenGenerator(max_new_tokens=10)
    generator.tokenizer = tokenizer
    generator.model = model

    assert generator.answer("prompt") == "Generated answer"
    assert tokenizer.template_options["truncation"] is True
    assert tokenizer.template_options["max_length"] == 90
    assert model.generation_options["max_new_tokens"] == 10
    assert tokenizer.decoded_tokens == [9, 10]
