from pathlib import Path
from typing import Any

from src.models import MinimalSource

MODEL_NAME = "Qwen/Qwen3-0.6B"


def read_source_text(
    source: MinimalSource,
    project_root: Path | None = None,
) -> str:
    root = project_root or Path.cwd()
    path = root / source.file_path
    text = path.read_text(encoding="utf-8")
    return text[source.first_character_index:source.last_character_index]


def build_prompt_to_answer(
    question: str,
    sources: list[MinimalSource],
    project_root: Path | None = None,
) -> str:
    context = (
        "\n\n".join(
            f"[{source.file_path}:{source.first_character_index}-"
            f"{source.last_character_index}]\n"
            f"{read_source_text(source, project_root)}"
            for source in sources
        )
        or "(No source was retrieved.)"
    )

    return (
        "Answer using only the given sources. "
        "If they are insufficient, say so.\n\n"
        f"Question:\n{question}\n\n"
        f"Sources:\n{context}\n\n"
        "Answer concisely:"
    )


class QwenGenerator:
    def __init__(
        self,
        model_name: str = MODEL_NAME,
        max_new_tokens: int = 256,
    ) -> None:
        self.model_name = model_name
        self.max_new_tokens = max_new_tokens
        self.tokenizer: Any | None = None
        self.model: Any | None = None

    def _load(self) -> None:
        if self.model is not None:
            return

        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype="auto",
            device_map="auto",
        )

    def answer(self, prompt: str) -> str:
        self._load()
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Model or tokenizer not loaded")

        max_input_tokens = (
            self.model.config.max_position_embeddings - self.max_new_tokens
        )
        input_tokens = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=True,
            add_generation_prompt=True,
            enable_thinking=False,
            truncation=True,
            max_length=max_input_tokens,
            return_dict=True,
            return_tensors="pt",
        ).to(self.model.device)
        output = self.model.generate(
            **input_tokens,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
        )
        prompt_size = input_tokens["input_ids"].shape[-1]
        answer: str = self.tokenizer.decode(
            output[0][prompt_size:],
            skip_special_tokens=True,
        )
        return answer.strip()


def generate_answer(
    question: str,
    sources: list[MinimalSource],
    generator: QwenGenerator,
    project_root: Path | None = None,
) -> str:
    return generator.answer(
        build_prompt_to_answer(question, sources, project_root)
    )
