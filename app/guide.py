from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Tuple
import copy

from app.guardrails import (
    compact_snippet,
    format_citation,
    is_confident,
    unsupported_response,
)
from app.retrieve import Retriever
from app.schema import SpecDraft


Question = Tuple[str, str, str]

QUESTIONS: List[Question] = [
    (
        "app_type",
        "I will help draft a simple blueprint-like specification; to describe the intent of the app, I need to know what it does.",
        "What does this application do for users?",
    ),
    ("components", "To outline the structure, I need the main parts involved.", "What are the main parts or services in the app?"),
    ("dependencies", "To keep the flow clear, I need to know how parts depend on each other.", "How do those parts depend on each other?"),
    ("inputs", "To capture user input needs, I need to know what people must provide at runtime.", "What information should a user provide when starting it?"),
    ("day2_actions", "To plan ongoing use, I need to know what actions matter after deployment.", "What ongoing actions should be possible later?"),
    ("target_environment", "To keep the draft grounded, I need the target environment label.", "Which environment should this run on?"),
]


def _parse_list(value: str) -> List[str]:
    if not value.strip():
        return []
    if "," in value:
        parts = value.split(",")
    elif ";" in value:
        parts = value.split(";")
    elif " and " in value:
        parts = value.split(" and ")
    else:
        parts = [value]
    return [item.strip() for item in parts if item.strip()]


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


def _format_examples(results, heading: str) -> str:
    if not results:
        return f"{heading}\nI am not confident. I did not find relevant examples."

    blocks = []
    for chunk in results:
        snippet = compact_snippet(chunk.text)
        citation = format_citation(chunk)
        blocks.append(f"{snippet}\n[{citation}]")

    if not is_confident(results):
        return (
            f"{heading}\nI am not confident. These are the closest examples I found.\n\n"
            + "\n\n".join(blocks)
        )

    return f"{heading}\n\n" + "\n\n".join(blocks)


def _format_summary(spec: SpecDraft) -> str:
    parts = []
    if spec.app_type:
        parts.append(f"App purpose: {spec.app_type}")
    if spec.components:
        parts.append(f"Main parts: {', '.join(spec.components)}")
    if spec.dependencies:
        parts.append(f"Dependencies: {', '.join(spec.dependencies)}")
    if spec.inputs:
        parts.append(f"Inputs: {', '.join(spec.inputs)}")
    if spec.day2_actions:
        parts.append(f"Ongoing actions: {', '.join(spec.day2_actions)}")
    if spec.target_environment:
        parts.append(f"Target environment: {spec.target_environment}")
    if not parts:
        return "Draft summary: No details captured yet."
    return "Draft summary: " + " | ".join(parts)


def _context_sentence(why: str, last_answer: Optional[str]) -> str:
    if last_answer:
        return f"{why} You said: {last_answer}."
    return why


def _prompt_query(key: str) -> str:
    if key == "components":
        return "class Service"
    if key == "dependencies":
        return "dependencies ="
    if key == "inputs":
        return "Variable.Simple"
    if key == "day2_actions":
        return "@action"
    if key == "target_environment":
        return "provider_type"
    return "class Blueprint"


def build_evidence(results, title: str) -> List[dict]:
    evidence = []
    for chunk in results:
        evidence.append(
            {
                "title": title,
                "file_path": chunk.file_path,
                "line_range": f"L{chunk.start_line}-L{chunk.end_line}",
            }
        )
    return evidence


@dataclass
class GuideState:
    spec: SpecDraft
    step_index: int
    turns: int
    last_answer_by_key: Dict[str, str]
    awaiting_correction: bool
    awaiting_revision: bool
    complete: bool


class GuideEngine:
    def __init__(self, retriever: Retriever) -> None:
        self.retriever = retriever
        self.state = GuideState(
            spec=SpecDraft(),
            step_index=0,
            turns=0,
            last_answer_by_key={},
            awaiting_correction=False,
            awaiting_revision=False,
            complete=False,
        )

    def _current_question(self) -> Question:
        return QUESTIONS[self.state.step_index]

    def _prompt_block(self) -> Tuple[str, List[dict], str]:
        key, context, question = self._current_question()
        last_answer = (
            self.state.last_answer_by_key.get(QUESTIONS[self.state.step_index - 1][0])
            if self.state.step_index > 0
            else None
        )
        prompt_examples = self.retriever.search(_prompt_query(key), top_k=1, repo="dsl-samples")
        prompt_text = "\n".join(
            [
                _context_sentence(context, last_answer),
                question,
                _format_examples(prompt_examples, "Example (from indexed samples):"),
            ]
        )
        evidence = build_evidence(prompt_examples, "Example (from indexed samples)")
        return prompt_text, evidence, key

    def start_prompt(self) -> Tuple[str, List[dict], str]:
        return self._prompt_block()

    def _after_answer_blocks(self, key: str, answer: str) -> Tuple[str, List[dict]]:
        examples = self.retriever.search(example_query(key, answer), top_k=3, repo="dsl-samples")
        text = _format_examples(examples, "Examples (from indexed samples):")
        evidence = build_evidence(examples, "Examples (from indexed samples)")
        return text, evidence

    def _summary_block(self) -> str:
        return _format_summary(self.state.spec)

    def handle_message(self, message: str) -> Tuple[str, List[dict], str]:
        if self.state.complete:
            return (
                "This is a draft you can keep iterating on.",
                [],
                "complete",
            )

        normalized = message.strip().lower()
        if self.state.awaiting_correction:
            if normalized in {"y", "yes"}:
                self.state.awaiting_correction = False
                self.state.awaiting_revision = True
                prompt_text, evidence, key = self._prompt_block()
                return prompt_text, evidence, key

            self.state.awaiting_correction = False
            self.state.step_index += 1
            prompt_text, evidence, key = self._prompt_block()
            return prompt_text, evidence, key

        key, _, _ = self._current_question()
        if self.state.awaiting_revision:
            self.state.awaiting_revision = False
            self.state.spec = update_spec(self.state.spec, key, message)
            self.state.last_answer_by_key[key] = message
        else:
            self.state.spec = update_spec(self.state.spec, key, message)
            self.state.last_answer_by_key[key] = message
            self.state.turns += 1

        blocks = []
        evidence: List[dict] = []
        after_text, after_evidence = self._after_answer_blocks(key, message)
        blocks.append(after_text)
        evidence.extend(after_evidence)

        if self.state.turns % 2 == 0 and self.state.step_index < len(QUESTIONS) - 1:
            blocks.append(self._summary_block())
            prompt_examples = self.retriever.search(_prompt_query(key), top_k=1, repo="dsl-samples")
            blocks.append(_format_examples(prompt_examples, "Example (from indexed samples):"))
            evidence.extend(build_evidence(prompt_examples, "Example (from indexed samples)"))
            blocks.append("Should I change your last answer before we continue?")
            self.state.awaiting_correction = True
            return "\n\n".join(blocks), evidence, "confirm_change"

        if self.state.step_index >= len(QUESTIONS) - 1:
            blocks.append(self._summary_block())
            final_examples = self.retriever.search(
                _prompt_query("target_environment"), top_k=1, repo="dsl-samples"
            )
            blocks.append(_format_examples(final_examples, "Example (from indexed samples):"))
            evidence.extend(build_evidence(final_examples, "Example (from indexed samples)"))
            blocks.append("This is a draft you can keep iterating on.")
            self.state.complete = True
            return "\n\n".join(blocks), evidence, "complete"

        self.state.step_index += 1
        prompt_text, prompt_evidence, next_key = self._prompt_block()
        blocks.append(prompt_text)
        evidence.extend(prompt_evidence)
        return "\n\n".join(blocks), evidence, next_key

    def clone(self) -> "GuideEngine":
        cloned = GuideEngine(self.retriever)
        cloned.state = copy.deepcopy(self.state)
        return cloned


def run_guide(retriever: Retriever) -> SpecDraft:
    engine = GuideEngine(retriever)
    prompt, _, _ = engine.start_prompt()
    print(prompt)
    while not engine.state.complete:
        answer = input("> ").strip()
        reply, _, _ = engine.handle_message(answer)
        print(reply)
        print("\n---\n")
    return engine.state.spec
