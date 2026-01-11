from typing import Iterable, Optional

from app.retrieve import RetrievedChunk

MIN_BM25_SCORE = 0.2


def is_confident(results: Iterable[RetrievedChunk]) -> bool:
    results = list(results)
    if not results:
        return False
    return results[0].score >= MIN_BM25_SCORE


def unsupported_response() -> str:
    return (
        "Direct answer: I am not confident. I did not find relevant DSL or blueprint code.\n"
        "\n"
        "Supporting examples (collapsed by default):\n"
        "<details>\n"
        "<summary>Supporting examples</summary>\n"
        "None.\n"
        "</details>\n"
        "\n"
        "Limitation: No matching code was retrieved."
    )


def format_response(direct_answer: str, examples: str, limitation: Optional[str] = None) -> str:
    parts = [
        f"Direct answer: {direct_answer}",
        "",
        "Supporting examples (collapsed by default):",
        "<details>",
        "<summary>Supporting examples</summary>",
        examples.strip() or "None.",
        "</details>",
    ]
    if limitation:
        parts.extend(["", f"Limitation: {limitation}"])
    return "\n".join(parts)


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
