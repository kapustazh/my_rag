import ast
from src.models import Chunk

python_example = """
import os
def f():
    return 1
    
print(f())

# Comment
"""


def chunk_python(text: str, max_chunk_size: int) -> list[Chunk]:
    tree = ast.parse(text)
    chunks = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            chunks.append(
                Chunk(
                    text=node.body,
                    first_character_index=node.lineno,
                    last_character_index=node.end_lineno,
                )
            )
    return chunks


def chunk_markdown(text: str, max_chunk_size: int) -> list[Chunk]:
    chunks = []
    for i in range(0, len(text), max_chunk_size):
        chunks.append(
            Chunk(
                text=text[i : i + max_chunk_size],
                first_character_index=i,
                last_character_index=i + max_chunk_size,
            )
        )
    return chunks


markdown_example = """
# Title

## Subtitle

Text
"""

if __name__ == "__main__":
    chunks = chunk_python(python_example, 10)
    print(chunks)
    chunks = chunk_markdown(markdown_example, 10)
    print(chunks)
