import ast
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
INDEX_DIR = PROJECT_ROOT / "index"
INDEX_FILE = INDEX_DIR / "index.jsonl"
MANIFEST_FILE = INDEX_DIR / "manifest.json"

PY_EXTENSIONS = {".py"}
SAMPLE_EXTENSIONS = {".py", ".yaml", ".yml"}
CHUNK_LINE_SIZE = 300


@dataclass
class Chunk:
    repo: str
    file_path: str
    start_line: int
    end_line: int
    text: str


def _iter_repo_files(repo_path: Path, repo_name: str) -> Iterable[Path]:
    if repo_name == "dsl-samples":
        extensions = SAMPLE_EXTENSIONS
    else:
        extensions = PY_EXTENSIONS

    for path in repo_path.rglob("*"):
        if path.is_file() and path.suffix in extensions:
            yield path


def _read_lines(path: Path) -> List[str]:
    return path.read_text(encoding="utf-8", errors="ignore").splitlines()


def _chunk_python_file(path: Path) -> List[Tuple[int, int, str]]:
    lines = _read_lines(path)
    if not lines:
        return []

    text = "\n".join(lines)
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _chunk_text_lines(lines)

    ranges: List[Tuple[int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if getattr(node, "col_offset", 0) == 0:
                start = getattr(node, "lineno", None)
                end = getattr(node, "end_lineno", None)
                if start and end:
                    ranges.append((start, end))

    ranges.sort()
    chunks: List[Tuple[int, int, str]] = []
    cursor = 1
    for start, end in ranges:
        if cursor < start:
            module_text = "\n".join(lines[cursor - 1:start - 1]).strip()
            if module_text:
                chunks.append((cursor, start - 1, module_text))
        block_text = "\n".join(lines[start - 1:end]).strip()
        if block_text:
            chunks.append((start, end, block_text))
        cursor = end + 1

    if cursor <= len(lines):
        module_text = "\n".join(lines[cursor - 1:]).strip()
        if module_text:
            chunks.append((cursor, len(lines), module_text))

    return chunks


def _chunk_text_lines(lines: List[str]) -> List[Tuple[int, int, str]]:
    chunks: List[Tuple[int, int, str]] = []
    total = len(lines)
    start = 1
    while start <= total:
        end = min(start + CHUNK_LINE_SIZE - 1, total)
        text = "\n".join(lines[start - 1:end]).strip()
        if text:
            chunks.append((start, end, text))
        start = end + 1
    return chunks


def _chunk_file(path: Path) -> List[Tuple[int, int, str]]:
    if path.suffix == ".py":
        return _chunk_python_file(path)
    return _chunk_text_lines(_read_lines(path))


def build_index() -> List[Chunk]:
    repos = {
        "calm-dsl": DATA_DIR / "calm-dsl",
        "dsl-samples": DATA_DIR / "dsl-samples",
    }
    chunks: List[Chunk] = []
    for repo_name, repo_path in repos.items():
        for path in _iter_repo_files(repo_path, repo_name):
            for start, end, text in _chunk_file(path):
                rel_path = path.relative_to(PROJECT_ROOT)
                chunks.append(
                    Chunk(
                        repo=repo_name,
                        file_path=str(rel_path),
                        start_line=start,
                        end_line=end,
                        text=text,
                    )
                )
    return chunks


def write_index(chunks: List[Chunk]) -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with INDEX_FILE.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk.__dict__, ensure_ascii=True) + "\n")

    manifest = {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "chunk_count": len(chunks),
        "index_file": str(INDEX_FILE.relative_to(PROJECT_ROOT)),
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def ensure_index() -> None:
    if not INDEX_FILE.exists():
        chunks = build_index()
        write_index(chunks)


def main() -> None:
    chunks = build_index()
    write_index(chunks)
    print(f"Indexed {len(chunks)} chunks to {INDEX_FILE}")


if __name__ == "__main__":
    main()
