import ast
import re
from itertools import accumulate

_PARAGRAPH_BREAK = re.compile(r"\n{2,}")


def _windows(text: str, max_size: int) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    for start in range(0, len(text), max_size):
        end = min(start + max_size, len(text))
        if text[start:end].strip():
            ranges.append((start, end))
    return ranges


def _line_starts(text: str) -> list[int]:
    return [0, *accumulate(map(len, text.splitlines(keepends=True)))]


def _add_span(
    text: str,
    start: int,
    end: int,
    max_chunk_size: int,
    span_ranges: list[tuple[int, int]],
) -> None:
    if start >= end or not text[start:end].strip():
        return
    if end - start <= max_chunk_size:
        span_ranges.append((start, end))
        return
    for s, e in _windows(text[start:end], max_chunk_size):
        span_ranges.append((start + s, start + e))


def _add_node(
    node: ast.AST,
    text: str,
    starts: list[int],
    max_chunk_size: int,
    span_ranges: list[tuple[int, int]],
) -> None:
    node_start = starts[node.lineno - 1]
    node_end = starts[node.end_lineno]

    if node_end - node_start <= max_chunk_size:
        _add_span(text, node_start, node_end, max_chunk_size, span_ranges)
        return

    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        before = len(span_ranges)
        for child in node.body:
            _add_node(child, text, starts, max_chunk_size, span_ranges)
        if len(span_ranges) > before:
            return

    _add_span(text, node_start, node_end, max_chunk_size, span_ranges)


def chunk_python(text: str, max_chunk_size: int) -> list[tuple[int, int]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _windows(text, max_chunk_size)
    if not tree.body:
        return _windows(text, max_chunk_size)

    starts = _line_starts(text)
    span_ranges: list[tuple[int, int]] = []
    start = 0
    for node in tree.body:
        end = starts[node.end_lineno]
        _add_span(
            text, start, starts[node.lineno - 1], max_chunk_size, span_ranges
        )
        _add_node(node, text, starts, max_chunk_size, span_ranges)
        start = end

    _add_span(text, start, len(text), max_chunk_size, span_ranges)
    return span_ranges


def chunk_markdown(text: str, max_chunk_size: int) -> list[tuple[int, int]]:
    if not text.strip():
        return []
    paragraphs: list[tuple[int, int]] = []
    pos = 0
    for match in _PARAGRAPH_BREAK.finditer(text):
        if text[pos:match.start()].strip():
            paragraphs.append((pos, match.start()))
        pos = match.end()
    if text[pos:].strip():
        paragraphs.append((pos, len(text)))
    span_ranges: list[tuple[int, int]] = []
    start, end = paragraphs[0]
    for p_start, p_end in paragraphs[1:]:
        if p_end - start <= max_chunk_size:
            end = p_end
        else:
            _add_span(text, start, end, max_chunk_size, span_ranges)
            start, end = p_start, p_end
    _add_span(text, start, end, max_chunk_size, span_ranges)
    return span_ranges


if __name__ == "__main__":
    py = "import os\n# gap\ndef f():\n    return 1\n\nprint(f())\n# end\n"
    md = "# title\n\nhello\n\n## subtitle\n\ntext"

    for start, end in chunk_python(py, 2000):
        print("py", repr(py[start:end]))

    for start, end in chunk_markdown(md, 2000):
        print("md", repr(md[start:end]))
