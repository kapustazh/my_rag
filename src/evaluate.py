from src.models import (
    AnsweredQuestion,
    MinimalSource,
    RagDataset,
    StudentSearchResults,
)


def _iou(a: MinimalSource, b: MinimalSource) -> float:
    """Calculate intersection over union for two character ranges.

    Args:
        a: First source range.
        b: Second source range.

    Returns:
        Range intersection over union from zero to one.
    """
    start = max(a.first_character_index, b.first_character_index)
    end = min(a.last_character_index, b.last_character_index)
    inter = max(0, end - start)
    union = (
        (a.last_character_index - a.first_character_index)
        + (b.last_character_index - b.first_character_index)
        - inter
    )
    iou = inter / union if union else 0.0
    return iou


def _hit(retrieved: list[MinimalSource], gt: MinimalSource) -> bool:
    """Determine whether retrieved sources contain a ground-truth hit.

    Args:
        retrieved: Sources returned by retrieval.
        gt: Expected source location.

    Returns:
        Whether a same-file source reaches the overlap threshold.
    """
    return any(
        src.file_path == gt.file_path and _iou(src, gt) >= 0.05
        for src in retrieved
    )


def recall_at_k(results: StudentSearchResults, dataset: RagDataset) -> float:
    """Calculate mean source recall for answered questions.

    Args:
        results: Student retrieval results to score.
        dataset: Dataset containing ground-truth sources.

    Returns:
        Mean recall across answered questions.

    Raises:
        ValueError: If the dataset has no ground-truth sources to score.
    """
    by_id = {
        item.question_id: item.retrieved_sources
        for item in results.search_results
    }
    scores: list[float] = []
    for question in dataset.rag_questions:
        if not isinstance(question, AnsweredQuestion):
            continue
        retrieved = by_id.get(question.question_id, [])
        hits = sum(1 for gt in question.sources if _hit(retrieved, gt))
        scores.append(hits / len(question.sources))
    if not scores:
        raise ValueError("Dataset has no ground-truth sources to score")
    return sum(scores) / len(scores)
