from threading import Lock
from typing import Annotated

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, StringConstraints

from src.generate import QwenGenerator
from src.models import StudentSearchResults, StudentSearchResultsAndAnswer
from src.services import answer_query, search_query


class QueryRequest(BaseModel):
    query: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1)
    ]
    k: Annotated[int, Field(ge=1)]


app = FastAPI()

_generator = QwenGenerator()
_model_lock = Lock()


@app.post("/search", response_model=StudentSearchResults)
def search(request: QueryRequest) -> StudentSearchResults:
    try:
        return search_query(request.query, request.k)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/answer", response_model=StudentSearchResultsAndAnswer)
def answer(request: QueryRequest) -> StudentSearchResultsAndAnswer:
    try:
        with _model_lock:
            return answer_query(request.query, request.k, _generator)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
