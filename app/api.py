from dataclasses import asdict
from typing import Dict, List, Optional, Tuple
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.guide import GuideEngine
from app.index import ensure_index
from app.retrieve import Retriever


app = FastAPI(title="Blueprint Buddy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

ensure_index()
RETRIEVER = Retriever()


class Session:
    def __init__(self) -> None:
        self.engine = GuideEngine(RETRIEVER)


SESSIONS: Dict[str, Session] = {}


class SessionResponse(BaseModel):
    session_id: str
    reply: Optional[str] = None
    draft_snapshot: Optional[dict] = None
    step: Optional[str] = None
    evidence: Optional[List[dict]] = None


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ResetRequest(BaseModel):
    session_id: str


class CompareVariant(BaseModel):
    confidence_range: str
    evidence_source: str
    risk_tolerance: str
    expression_style: str


class CompareRequest(BaseModel):
    session_id: str
    message: str
    variant: CompareVariant


@app.post("/session", response_model=SessionResponse)
def create_session() -> SessionResponse:
    session_id = str(uuid.uuid4())
    session = Session()
    SESSIONS[session_id] = session
    prompt, evidence, step = session.engine.start_prompt()
    return SessionResponse(
        session_id=session_id,
        reply=prompt,
        draft_snapshot=asdict(session.engine.state.spec),
        step=step,
        evidence=evidence or None,
    )


@app.get("/")
def root() -> dict:
    return {
        "ok": True,
        "docs": "/docs",
        "endpoints": ["/session", "/chat", "/reset", "/compare"],
    }


@app.post("/chat", response_model=SessionResponse)
def chat(request: ChatRequest) -> SessionResponse:
    session = SESSIONS.get(request.session_id)
    if not session:
        return SessionResponse(session_id=request.session_id)

    reply, evidence, step = session.engine.handle_message(request.message)
    return SessionResponse(
        session_id=request.session_id,
        reply=reply,
        draft_snapshot=asdict(session.engine.state.spec),
        step=step,
        evidence=evidence or None,
    )


@app.post("/reset", response_model=SessionResponse)
def reset(request: ResetRequest) -> SessionResponse:
    if request.session_id in SESSIONS:
        SESSIONS[request.session_id] = Session()
    session = SESSIONS.get(request.session_id)
    if not session:
        return SessionResponse(session_id=request.session_id)
    prompt, evidence, step = session.engine.start_prompt()
    return SessionResponse(
        session_id=request.session_id,
        reply=prompt,
        draft_snapshot=asdict(session.engine.state.spec),
        step=step,
        evidence=evidence or None,
    )


@app.post("/compare", response_model=SessionResponse)
def compare(request: CompareRequest) -> SessionResponse:
    session = SESSIONS.get(request.session_id)
    if not session:
        return SessionResponse(session_id=request.session_id)

    clone = session.engine.clone()
    reply, evidence, step = clone.handle_message(request.message)
    reply, evidence = apply_variant(reply, evidence or [], request.variant)
    return SessionResponse(
        session_id=request.session_id,
        reply=reply,
        draft_snapshot=asdict(clone.state.spec),
        step=step,
        evidence=evidence or None,
    )


def _parse_line_range(line_range: str) -> Tuple[int, int]:
    start, end = line_range.replace("L", "").split("-L")
    return int(start), int(end)


def _find_chunk_text(file_path: str, line_range: str) -> Optional[str]:
    try:
        start, end = _parse_line_range(line_range)
    except ValueError:
        return None
    for doc in RETRIEVER._docs:
        if doc["file_path"] == file_path and doc["start_line"] == start and doc["end_line"] == end:
            return doc["text"]
    return None


def _truncate_blocks(text: str, max_blocks: int) -> str:
    blocks = [block for block in text.split("\n\n") if block.strip()]
    return "\n\n".join(blocks[:max_blocks])


def apply_variant(reply: str, evidence: List[dict], variant: CompareVariant) -> Tuple[str, List[dict]]:
    adjusted = reply
    adjusted_evidence = evidence

    if variant.confidence_range.lower() == "focused":
        adjusted = _truncate_blocks(adjusted, 2)
    elif variant.confidence_range.lower() == "broad":
        context_lines = [
            f"- {item['title']}: {item['file_path']}:{item['line_range']}"
            for item in adjusted_evidence
        ]
        if context_lines:
            adjusted += "\n\nAdditional context (same sources):\n" + "\n".join(context_lines)

    if variant.risk_tolerance.lower() == "cautious":
        adjusted = "Caution: This response only uses indexed DSL and samples.\n\n" + adjusted
    elif variant.risk_tolerance.lower() == "adventurous":
        adjusted += "\n\nUncertainty: I may be missing details; treat this as a draft."

    if variant.expression_style.lower() == "concrete":
        if adjusted_evidence:
            first = adjusted_evidence[0]
            snippet = _find_chunk_text(first["file_path"], first["line_range"])
            if snippet:
                lines = "\n".join(snippet.splitlines()[:4])
                adjusted += f"\n\nQuoted evidence:\n{lines}"

    if variant.evidence_source.lower() == "public knowledge":
        adjusted += "\n\nPublic: No public knowledge source is configured in this build."
        adjusted_evidence = []
    elif variant.evidence_source.lower() == "both":
        adjusted += "\n\nPublic: No public knowledge source is configured in this build."

    return adjusted, adjusted_evidence
