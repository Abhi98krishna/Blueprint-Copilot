import argparse
from pathlib import Path

from app import index as indexer
from app.answer import answer_question
from app.guide import run_guide
from app.retrieve import Retriever
from app.schema import export_spec


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"


def run_ask(retriever: Retriever) -> None:
    print("Ask mode: type your question (or 'exit').")
    while True:
        question = input("> ").strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            break
        response = answer_question(question, retriever)
        print(response)
        print("")


def main() -> None:
    parser = argparse.ArgumentParser(description="Blueprint Buddy CLI")
    parser.add_argument(
        "--mode",
        choices=["guide", "ask"],
        default="guide",
        help="chat mode",
    )
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="rebuild the local index",
    )
    args = parser.parse_args()

    if args.reindex:
        chunks = indexer.build_index()
        indexer.write_index(chunks)
    else:
        indexer.ensure_index()

    retriever = Retriever()

    if args.mode == "guide":
        spec = run_guide(retriever)
        json_path, md_path = export_spec(spec, OUTPUT_DIR)
        print("Spec draft saved:")
        print(f"- {json_path}")
        print(f"- {md_path}")
    else:
        run_ask(retriever)


if __name__ == "__main__":
    main()
