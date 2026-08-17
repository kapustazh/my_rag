import ast
import re
from itertools import accumulate

_HEADING = re.compile(r"(?m)^#{1,6}[ \t]")
_DEF_NODES = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


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


def chunk_python(text: str, max_chunk_size: int) -> list[tuple[int, int]]:
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

    _add_span(text, 0, starts[defs[0].lineno - 1], max_chunk_size, span_ranges)
    for node in defs:
        _add_span(
            text,
            starts[node.lineno - 1],
            starts[node.end_lineno],
            max_chunk_size,
            span_ranges,
        )
    _add_span(
        text,
        starts[defs[-1].end_lineno],
        len(text),
        max_chunk_size,
        span_ranges,
    )
    return span_ranges


def _section_ranges(text: str) -> list[tuple[int, int]]:
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
    if not text.strip():
        return []
    span_ranges: list[tuple[int, int]] = []
    for start, end in _section_ranges(text):
        _add_span(text, start, end, max_chunk_size, span_ranges)
    return span_ranges


if __name__ == "__main__":
    py = "import os\n# gap\ndef f():\n    return 1\n\nprint(f())\n# end\n"
    md = "# title\n\nhello\n\n## subtitle\n\ntext"

    ranges = chunk_python(py, 2000)
    assert any("def f" in py[s:e] for s, e in ranges)
    for start, end in ranges:
        print("py", repr(py[start:end]))

    for start, end in chunk_markdown(md, 2000):
        print("md", repr(md[start:end]))
