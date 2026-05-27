from .question import AnsweredQuestion, UnansweredQuestion
from pydantic import BaseModel
from typing import List


class RagDataset(BaseModel):
    rag_questions: List[AnsweredQuestion | UnansweredQuestion]
