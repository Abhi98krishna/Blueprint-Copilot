import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from rank_bm25 import BM25Okapi

from app.index import INDEX_FILE

TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


@dataclass
class RetrievedChunk:
    repo: str
    file_path: str
    start_line: int
    end_line: int
    text: str
    score: float


class Retriever:
    def __init__(self, index_path: Path = INDEX_FILE) -> None:
        self.index_path = index_path
        self._docs = self._load_index()
        self._corpus_tokens = [self._tokenize(doc["text"]) for doc in self._docs]
        self._bm25 = BM25Okapi(self._corpus_tokens)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return TOKEN_RE.findall(text.lower())

    def _load_index(self) -> List[dict]:
        docs = []
        with self.index_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                docs.append(json.loads(line))
        return docs

    def search(self, query: str, top_k: int = 3, repo: Optional[str] = None) -> List[RetrievedChunk]:
        tokens = self._tokenize(query)
        if not tokens:
            return []

        scores = self._bm25.get_scores(tokens)
        results: List[RetrievedChunk] = []
        for idx, score in enumerate(scores):
            if score <= 0:
                continue
            doc = self._docs[idx]
            if repo and doc["repo"] != repo:
                continue
            results.append(
                RetrievedChunk(
                    repo=doc["repo"],
                    file_path=doc["file_path"],
                    start_line=doc["start_line"],
                    end_line=doc["end_line"],
                    text=doc["text"],
                    score=float(score),
                )
            )

        results.sort(key=lambda item: item.score, reverse=True)
        return results[:top_k]
