import uuid
from typing import List

from pydantic import BaseModel, Field, model_validator


class MinimalSource(BaseModel):
    file_path: str
    first_character_index: int
    last_character_index: int


class UnansweredQuestion(BaseModel):
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str


class AnsweredQuestion(UnansweredQuestion):
    sources: List[MinimalSource]
    answer: str


class Chunk(MinimalSource):
    text: str

    @model_validator(mode="after")
    def validate_text_range(self) -> "Chunk":
        expected_length = (
            self.last_character_index - self.first_character_index
        )

        if len(self.text) != expected_length:
            raise ValueError(
                f"Chunk text length {len(self.text)} "
                + f"must match its character range {expected_length}"
            )

        if len(self.text) > 2000:
            raise ValueError("Chunk cannot exceed 2000 characters")

        return self


class RagDataset(BaseModel):
    rag_questions: List[AnsweredQuestion | UnansweredQuestion]


class MinimalSearchResults(BaseModel):
    question_id: str
    question: str
    retrieved_sources: List[MinimalSource]


class MinimalAnswer(MinimalSearchResults):
    answer: str


class StudentSearchResults(BaseModel):
    search_results: List[MinimalSearchResults]
    k: int


class StudentSearchResultsAndAnswer(StudentSearchResults):
    search_results: List[MinimalAnswer]  # type: ignore[assignment]
