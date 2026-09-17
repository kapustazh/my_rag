import uuid
from typing import List

from pydantic import BaseModel, Field, model_validator


class MinimalSource(BaseModel):
    """Identify an exact character range in a corpus file.

    Attributes:
        file_path: Corpus-relative file path.
        first_character_index: Inclusive start offset.
        last_character_index: Exclusive end offset.
    """

    file_path: str
    first_character_index: int
    last_character_index: int


class UnansweredQuestion(BaseModel):
    """Represent a question that has not been answered.

    Attributes:
        question_id: Stable question identifier.
        question: Natural-language question text.
    """

    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str


class AnsweredQuestion(UnansweredQuestion):
    """Represent a question with ground-truth sources and an answer.

    Attributes:
        sources: Ground-truth source locations.
        answer: Reference answer text.
    """

    sources: List[MinimalSource]
    answer: str


class Chunk(MinimalSource):
    """Store indexed text together with its source location.

    Attributes:
        text: Exact text inside the inherited character range.
    """

    text: str

    @model_validator(mode="after")
    def validate_text_range(self) -> "Chunk":
        """Ensure chunk text matches its range and size limit.

        Returns:
            The validated chunk.

        Raises:
            ValueError: If text length and offsets differ or exceed 2,000.
        """
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
    """Contain answered and unanswered RAG questions.

    Attributes:
        rag_questions: Questions contained in the dataset.
    """

    rag_questions: List[AnsweredQuestion | UnansweredQuestion]


class MinimalSearchResults(BaseModel):
    """Store one question and its retrieved source locations.

    Attributes:
        question_id: Identifier copied from the input question.
        question: Original question text.
        retrieved_sources: Ranked source locations returned by retrieval.
    """

    question_id: str
    question: str
    retrieved_sources: List[MinimalSource]


class MinimalAnswer(MinimalSearchResults):
    """Extend search results with a generated answer.

    Attributes:
        answer: Answer generated from the retrieved sources.
    """

    answer: str


class StudentSearchResults(BaseModel):
    """Contain batched student search results and the requested k.

    Attributes:
        search_results: Retrieval results for each input question.
        k: Maximum number of sources requested per question.
    """

    search_results: List[MinimalSearchResults]
    k: int


class StudentSearchResultsAndAnswer(StudentSearchResults):
    """Contain batched search results with generated answers.

    Attributes:
        search_results: Answered retrieval results for each question.
    """

    search_results: List[MinimalAnswer]  # type: ignore[assignment]
