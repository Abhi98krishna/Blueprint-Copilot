from app.guardrails import (
    compact_snippet,
    format_citation,
    format_response,
    is_confident,
    unsupported_response,
)
from app.retrieve import Retriever


def answer_question(question: str, retriever: Retriever) -> str:
    results = retriever.search(question, top_k=3)
    if not results:
        return unsupported_response()

    blocks = []
    for chunk in results:
        snippet = compact_snippet(chunk.text)
        citation = format_citation(chunk)
        blocks.append(f"{snippet}\n[{citation}]")

    if not is_confident(results):
        return format_response(
            "I am not confident. These are the closest matches I found.",
            "\n\n".join(blocks),
            "Top retrieval score is below the confidence threshold.",
        )

    return format_response("Closest matches from indexed DSL and blueprints.", "\n\n".join(blocks))
