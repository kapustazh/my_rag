*This project has been created as part of the 42 curriculum by mnestere*

# Description

Local Retrieval-Augmented Generation (RAG) system for the vLLM 0.10.1 codebase.
It indexes Python and Markdown files, retrieves relevant sources with BM25, and
uses Qwen/Qwen3-0.6B for grounded answers.

Use the Python Fire CLI or the local FastAPI service for search and answers.

# Instructions

## Development

```bash
make install      # install dependencies
make lint-strict  # run strict linting locally
```

## Run the main pipeline

Run from the repository root. If `data/raw/` is missing, extract the corpus:

```bash
uv sync --python 3.10

mkdir -p data/raw
unzip -q vllm-0.10.1.zip -d data/raw

# Build the BM25 index.
uv run python -m src index --max_chunk_size 2000

# Search one question.
uv run python -m src search \
  "What HTTP endpoint dynamically loads a LoRA adapter?" \
  --k 5

# Search the complete public documentation dataset.
uv run python -m src search_dataset \
  --dataset_path data/datasets/UnansweredQuestions/dataset_docs_public.json \
  --k 5 \
  --save_directory data/output/search_results/UnansweredQuestions

# Evaluate the search results against the answered dataset.
uv run python -m src evaluate \
  --student_search_results_path \
  data/output/search_results/UnansweredQuestions/dataset_docs_public.json \
  --dataset_path data/datasets/AnsweredQuestions/dataset_docs_public.json

# Optional: generate one answer with Qwen.
uv run python -m src answer \
  "What HTTP endpoint dynamically loads a LoRA adapter?" \
  --k 5

# Generate answers for the complete search-results file.
uv run python -m src answer_dataset \
  --student_search_results_path \
  data/output/search_results/UnansweredQuestions/dataset_docs_public.json \
  --save_directory data/output/search_results_and_answer/UnansweredQuestions
```

## Run the FastAPI API

Start the API in one terminal:

```bash
uv run uvicorn src.api:app \
  --host 127.0.0.1 \
  --port 8000 \
  --reload
```

Then send one structured `POST /search` request from another terminal:

```bash
curl --request POST \
  --url http://127.0.0.1:8000/search \
  --header 'Content-Type: application/json' \
  --data '{
    "query": "What HTTP endpoint dynamically loads a LoRA adapter?",
    "k": 5
  }'
```

API documentation is available at <http://127.0.0.1:8000/docs>.

# System architecture

Pipeline stages:

```text
data/raw/vllm-0.10.1/
        │
        ▼
ingest files and create character-preserving chunks
        │
        ▼
build and persist BM25 index in data/processed/lexical/
        │
        ▼
question ──► tokenize ──► retrieve top-k source locations
                                      │
                                      ▼
                         build grounded Qwen prompt
                                      │
                                      ▼
                         generate structured JSON answer
```

`index` ingests files and builds the index. `search` and `search_dataset` find
sources. `answer` and `answer_dataset` send retrieved text to Qwen. `evaluate`
calculates recall. Results use Pydantic models.

`src/api.py` exposes `POST /search` and `POST /answer` through the same service
layer. A lock protects local model use during answer requests.

# Chunking strategy

Python and Markdown files use different chunking strategies:

- Python files are parsed with the standard-library `ast` module. Top-level
  functions and classes stay together when possible. Large or invalid files
  fall back to fixed-size windows.
- Markdown and text files are first split at Markdown headings. Sections larger
  than the configured limit are split into fixed-size windows.

The default `--max_chunk_size` is 2,000 characters. Each chunk stores its exact
file path and character range.

# Retrieval method

The project uses BM25 through `bm25s`. Text is lowercased and tokenized with an
identifier-friendly regular expression. Underscored identifiers are indexed as
complete tokens and parts. File-name and parent-directory tokens improve source
matching, while common question words are removed.

The persisted index stores BM25 data and source metadata. A query returns up to
`k` `MinimalSource` records. Dataset commands use `tqdm` progress bars.

# Performance analysis

Measured locally with the vLLM 0.10.1 archive and public datasets. Results vary
by machine.

| Metric | Result | Requirement |
| --- | ---: | ---: |
| Indexed chunks | 17,947 | — |
| Ingestion and index creation | about 2.8 s | at most 5 min |
| Documentation recall@5 | 0.860 | at least 0.800 |
| Code recall@5 | 0.747 | at least 0.500 |
| Documentation batch search | about 2.9 s for 100 questions | at most 90 s for 200 questions |

Recall checks matching file paths and overlapping character ranges. A hit needs
character-range intersection-over-union of at least 0.05.

# Design decisions

BM25 is lightweight, CPU-friendly, and effective for identifiers such as
function names, endpoints, and configuration keys. The index stores source
metadata, keeping results compatible with the Pydantic models.

Qwen loads lazily, so indexing and search do not need model weights. Prompts use
exact retrieved spans and limit answers to those sources. Python Fire provides
the CLI; runtime validation handles its permissive argument casting.

The project focuses on lexical retrieval with BM25 and a lightweight local HTTP
API. Semantic embeddings, hybrid retrieval, incremental indexing, and caching
are not used.

# Challenges faced

The main challenge was preserving character offsets with structure-aware
chunks. Chunk ranges are calculated from the original file text and persisted
with the index.

Python uses AST nodes; Markdown uses headings. Both use the same maximum-size
fallback, so retrieved sources stay within the limit.

Python Fire can pass an integer query or string `k`. The CLI validates types
before invoking services.

# Example usage

The full workflow is in [Run the main pipeline](#run-the-main-pipeline).
Start the API with `uv run
uvicorn src.api:app --host 127.0.0.1 --port 8000` and use the request in [Run
the FastAPI API](#run-the-fastapi-api).

# Resources

- Introduction to Natural Language Processing: https://www.geeksforgeeks.org/nlp/introduction-to-natural-language-processing-nlp/
- BM25 info: https://www.geeksforgeeks.org/nlp/what-is-bm25-best-matching-25-algorithm/
- RAG evaluation metrics: https://medium.com/@ayushigupta9723/rags-evaluation-metrics-and-standard-industrial-pipeline-to-do-evaluation-f37c3791a2f8
- Pydantic documentation: https://docs.pydantic.dev/
- Python Fire documentation: https://github.com/google/python-fire
- FastAPI documentation: https://fastapi.tiangolo.com/
- Qwen3 documentation: https://qwen.readthedocs.io/

## AI usage

AI helped review RAG behavior, chunking, retrieval, Python Fire type coercion,
and README documentation. Results and decisions were checked against the local
code and datasets.
