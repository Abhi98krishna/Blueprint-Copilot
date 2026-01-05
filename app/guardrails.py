from typing import Iterable

from app.retrieve import RetrievedChunk

MIN_BM25_SCORE = 0.2


def is_confident(results: Iterable[RetrievedChunk]) -> bool:
    results = list(results)
    if not results:
        return False
    return results[0].score >= MIN_BM25_SCORE


def unsupported_response() -> str:
    return "I can't support that from the DSL/blueprint code I indexed."


def format_citation(chunk: RetrievedChunk) -> str:
    return f"{chunk.file_path}:L{chunk.start_line}-L{chunk.end_line}"


def compact_snippet(text: str, max_lines: int = 8) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text.strip()
    snippet = "\n".join(lines[:max_lines]).strip()
    return snippet + "\n..."


def ensure_citations(answer: str, citations: Iterable[str]) -> str:
    citations = [c for c in citations if c]
    if not citations:
        return answer
    if "L" in answer:
        return answer
    return answer.rstrip() + "\n\nSources: " + "; ".join(citations)
