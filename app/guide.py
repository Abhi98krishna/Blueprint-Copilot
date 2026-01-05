from dataclasses import replace
from typing import List, Tuple

from app.guardrails import compact_snippet, format_citation, is_confident, unsupported_response
from app.retrieve import Retriever
from app.schema import SpecDraft


Question = Tuple[str, str]

QUESTIONS: List[Question] = [
    ("app_type", "What kind of application is this blueprint for?"),
    ("components", "List the main components/services (comma-separated)."),
    ("dependencies", "Any dependencies between components? (comma-separated, e.g. web->db)"),
    ("inputs", "What runtime inputs/variables should users provide? (comma-separated)"),
    ("day2_actions", "Any day-2 actions to support? (comma-separated)"),
    ("target_environment", "Target environment label (e.g., AHV, ESXi, AWS)?"),
]


def _parse_list(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def update_spec(spec: SpecDraft, key: str, value: str) -> SpecDraft:
    if key in {"components", "dependencies", "inputs", "day2_actions"}:
        return replace(spec, **{key: _parse_list(value)})
    return replace(spec, **{key: value.strip()})


def example_query(key: str, value: str) -> str:
    if key == "components":
        return f"Service Package Deployment {value}"
    if key == "dependencies":
        return f"dependencies {value}"
    if key == "inputs":
        return f"Variable runtime {value}"
    if key == "day2_actions":
        return f"action {value}"
    if key == "target_environment":
        return f"provider_spec provider_type {value}"
    return f"Blueprint {value}"


def _format_examples(results) -> str:
    if not is_confident(results):
        return unsupported_response()

    blocks = []
    for chunk in results:
        snippet = compact_snippet(chunk.text)
        citation = format_citation(chunk)
        blocks.append(f"{snippet}\n[{citation}]")
    return "\n\n".join(blocks)


def run_guide(retriever: Retriever) -> SpecDraft:
    spec = SpecDraft()
    print("Guide mode: let's draft a blueprint-like spec.")
    for key, prompt in QUESTIONS:
        answer = input(f"{prompt}\n> ").strip()
        spec = update_spec(spec, key, answer)
        query = example_query(key, answer)
        examples = retriever.search(query, top_k=3, repo="dsl-samples")
        print("\nPatterns from dsl-samples:")
        print(_format_examples(examples))
        print("\n---\n")
    return spec
