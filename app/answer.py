from app.guardrails import compact_snippet, format_citation, is_confident, unsupported_response
from app.retrieve import Retriever


def answer_question(question: str, retriever: Retriever) -> str:
    results = retriever.search(question, top_k=3)
    if not is_confident(results):
        return unsupported_response()

    blocks = []
    for chunk in results:
        snippet = compact_snippet(chunk.text)
        citation = format_citation(chunk)
        blocks.append(f"{snippet}\n[{citation}]")
    return "\n\n".join(blocks)
