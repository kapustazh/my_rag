import ast
import re
from itertools import accumulate

_HEADING = re.compile(r"(?m)^#{1,6}[ \t]")
_DEF_NODES = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _windows(text: str, max_size: int) -> list[tuple[int, int]]:
    """Split text into non-empty fixed-size character ranges.

    Args:
        text: Text to split.
        max_size: Maximum number of characters per range.

    Returns:
        Start and end offsets for each non-empty range.
    """
    ranges: list[tuple[int, int]] = []
    for start in range(0, len(text), max_size):
        end = min(start + max_size, len(text))
        if text[start:end].strip():
            ranges.append((start, end))
    return ranges


def _line_starts(text: str) -> list[int]:
    """Return the character offset where each source line starts.

    Args:
        text: Source text whose lines should be located.

    Returns:
        Character offsets, including zero and the final line boundary.
    """
    return [0, *accumulate(map(len, text.splitlines(keepends=True)))]


def _add_span(
    text: str,
    start: int,
    end: int,
    max_chunk_size: int,
    span_ranges: list[tuple[int, int]],
) -> None:
    """Append a non-empty span, splitting it when it is too large.

    Args:
        text: Complete source text.
        start: Inclusive span start.
        end: Exclusive span end.
        max_chunk_size: Maximum number of characters per chunk.
        span_ranges: Range list to update in place.
    """
    if start >= end or not text[start:end].strip():
        return
    if end - start <= max_chunk_size:
        span_ranges.append((start, end))
        return
    for s, e in _windows(text[start:end], max_chunk_size):
        span_ranges.append((start + s, start + e))


def chunk_python(text: str, max_chunk_size: int) -> list[tuple[int, int]]:
    """Split Python source around top-level functions and classes.

    Args:
        text: Python source text.
        max_chunk_size: Maximum number of characters per chunk.

    Returns:
        Start and end offsets for the generated chunks.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _windows(text, max_chunk_size)

    starts = _line_starts(text)
    span_ranges: list[tuple[int, int]] = []
    defs = [
        node
        for node in tree.body
        if isinstance(node, _DEF_NODES) and node.end_lineno is not None
    ]
    if not defs:
        _add_span(text, 0, len(text), max_chunk_size, span_ranges)
        return span_ranges or _windows(text, max_chunk_size)

    cursor = 0
    for node in defs:
        end_lineno = node.end_lineno
        if end_lineno is None:
            continue
        start_lineno = min(
            [node.lineno, *(item.lineno for item in node.decorator_list)]
        )
        start = starts[start_lineno - 1]
        end = starts[end_lineno]
        _add_span(text, cursor, start, max_chunk_size, span_ranges)
        _add_span(
            text,
            start,
            end,
            max_chunk_size,
            span_ranges,
        )
        cursor = end
    _add_span(text, cursor, len(text), max_chunk_size, span_ranges)
    return span_ranges


def _section_ranges(text: str) -> list[tuple[int, int]]:
    """Locate Markdown sections delimited by headings.

    Args:
        text: Markdown or plain-text content.

    Returns:
        Start and end offsets for each section.
    """
    starts = [match.start() for match in _HEADING.finditer(text)]
    if not starts:
        return [(0, len(text))]
    ranges: list[tuple[int, int]] = []
    if starts[0] > 0:
        ranges.append((0, starts[0]))
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        ranges.append((start, end))
    return ranges


def chunk_markdown(text: str, max_chunk_size: int) -> list[tuple[int, int]]:
    """Split Markdown or text by headings and maximum size.

    Args:
        text: Markdown or plain-text content.
        max_chunk_size: Maximum number of characters per chunk.

    Returns:
        Start and end offsets for the generated chunks.
    """
    if not text.strip():
        return []
    span_ranges: list[tuple[int, int]] = []
    for start, end in _section_ranges(text):
        _add_span(text, start, end, max_chunk_size, span_ranges)
    return span_ranges
