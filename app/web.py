from pathlib import Path
import random
import re
import time
from datetime import datetime

import streamlit as st

from app import index as indexer
from app.guide import QUESTIONS, example_query, update_spec
from app.guardrails import compact_snippet, format_citation, is_confident, unsupported_response
from app.retrieve import Retriever
from app.schema import SpecDraft, export_spec


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"

st.set_page_config(page_title="Blueprint Buddy", layout="wide")

indexer.ensure_index()
retriever = Retriever()

st.markdown(
    """
    <style>
    :root {
        color-scheme: light;
    }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main {
        background: #2e2e2e;
    }
    [data-testid="stSidebar"] {
        display: none;
    }
    .main .block-container {
        max-width: 500px;
        padding: 0;
        background: #ffffff;
        border-radius: 18px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
        height: 90vh;
        margin: 2rem auto;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }
    h1, h2, h3, p, label, [data-testid="stMarkdownContainer"] {
        font-family: "Nutanix Soft", "Avenir Next", "Helvetica Neue", sans-serif;
        color: #0f172a;
    }
    .chat-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #e5e7eb;
        background: #ffffff;
    }
    .chat-title {
        display: flex;
        gap: 0.75rem;
        align-items: center;
    }
    .chat-title-text {
        display: flex;
        flex-direction: column;
        gap: 0.1rem;
    }
    .chat-title-text h1 {
        font-size: 15px;
        margin: 0;
        font-weight: 600;
        color: #111827;
    }
    .chat-title-text span {
        font-size: 12px;
        color: #6b7280;
    }
    .badge {
        border: 1px solid #e5e7eb;
        border-radius: 999px;
        padding: 0.1rem 0.5rem;
        font-size: 11px;
        color: #374151;
        background: #f9fafb;
    }
    .chat-body {
        flex: 1;
        overflow-y: auto;
        padding: 1rem;
        background: #ffffff;
    }
    .message-row {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
        align-items: flex-start;
    }
    .message-row.user {
        justify-content: flex-end;
    }
    .message-avatar {
        width: 28px;
        height: 28px;
        border-radius: 999px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #e5f2ff;
        color: #1f2937;
        font-size: 14px;
        flex-shrink: 0;
    }
    .message-bubble {
        max-width: 85%;
        padding: 0.5rem 0.75rem;
        border-radius: 12px;
        font-size: 13px;
        line-height: 1.5;
        color: #1f2937;
        background: #f3f4f6;
    }
    .message-bubble.user {
        background: #3b82f6;
        color: #ffffff;
    }
    .message-timestamp {
        font-size: 11px;
        color: #6b7280;
        margin-top: 0.25rem;
    }
    .system-bubble {
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        color: #374151;
    }
    .typing {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 12px;
        color: #6b7280;
    }
    .typing::before {
        content: "";
        width: 10px;
        height: 10px;
        border: 2px solid #93c5fd;
        border-top-color: #2563eb;
        border-radius: 50%;
        display: inline-block;
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    .chat-footer {
        padding: 0.75rem;
        border-top: 1px solid #e5e7eb;
        background: #ffffff;
    }
    .input-row {
        display: flex;
        gap: 0.5rem;
        align-items: center;
    }
    .input-row input {
        font-size: 13px;
    }
    .send-btn button {
        background: #3b82f6;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        height: 36px;
        padding: 0 12px;
    }
    .send-btn button:hover {
        background: #2563eb;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_text(text: str) -> str:
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\\1</strong>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<em>\\1</em>", escaped)
    return escaped.replace("\n", "<br>")


def timestamp() -> str:
    return datetime.now().strftime("%H:%M")


def build_patterns_message(results) -> str:
    if not is_confident(results):
        return unsupported_response()
    blocks = []
    for chunk in results:
        snippet = compact_snippet(chunk.text)
        citation = format_citation(chunk)
        blocks.append(f"<pre><code>{format_text(snippet)}</code></pre><div>[{citation}]</div>")
    return "Patterns from dsl-samples:<br><br>" + "<br><br>".join(blocks)


def validate_input(value: str) -> str:
    if not value or not value.strip():
        return "Please enter a message."
    if len(value) > 500:
        return "Message is too long (max 500 characters)."
    return ""


if "spec" not in st.session_state:
    st.session_state.spec = SpecDraft()
if "step" not in st.session_state:
    st.session_state.step = 0
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_typing" not in st.session_state:
    st.session_state.is_typing = False
if "assistant_icon" not in st.session_state:
    st.session_state.assistant_icon = random.choice(["✳️", "🔷", "🤖", "🧭", "✨"])

if not st.session_state.messages:
    st.session_state.messages.append(
        {
            "id": 1,
            "type": "ai",
            "content": "Guide mode: let's draft a blueprint-like spec.",
            "timestamp": timestamp(),
        }
    )
    st.session_state.messages.append(
        {
            "id": 2,
            "type": "ai",
            "content": QUESTIONS[0][1],
            "timestamp": timestamp(),
        }
    )

st.markdown(
    f"""
    <div class="chat-header" role="banner">
        <div class="chat-title">
            <div class="message-avatar" aria-label="Nutanix icon">🌀</div>
            <div class="chat-title-text">
                <h1>Copilot</h1>
                <span>Blueprint Assistant</span>
            </div>
        </div>
        <div style="display:flex; gap:0.4rem;">
            <span class="badge" aria-label="Conversation mode">Guide</span>
            <span class="badge" aria-label="Status">Active</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container():
    st.markdown('<div class="chat-body" role="log" aria-live="polite">', unsafe_allow_html=True)
    for message in st.session_state.messages:
        msg_type = message["type"]
        is_user = msg_type == "user"
        avatar = "" if is_user else f'<div class="message-avatar" aria-hidden="true">{st.session_state.assistant_icon}</div>'
        bubble_class = "message-bubble user" if is_user else "message-bubble"
        row_class = "message-row user" if is_user else "message-row"
        content = format_text(message["content"])
        if msg_type == "system":
            bubble_class = "message-bubble system-bubble"
        st.markdown(
            f"""
            <div class="{row_class}">
                {avatar}
                <div>
                    <div class="{bubble_class}" role="article">{content}</div>
                    <div class="message-timestamp">{message["timestamp"]}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    if st.session_state.is_typing:
        st.markdown(
            """
            <div class="message-row">
                <div class="message-avatar" aria-hidden="true">…</div>
                <div class="message-bubble">
                    <span class="typing">Thinking...</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="chat-footer" role="contentinfo">', unsafe_allow_html=True)
input_col, button_col = st.columns([1, 0.2], gap="small")
with input_col:
    user_input = st.text_input(
        "Ask me anything about blueprints...",
        label_visibility="collapsed",
        placeholder="Ask me anything about blueprints...",
        disabled=st.session_state.is_typing,
    )
with button_col:
    send_clicked = st.button("Send", disabled=st.session_state.is_typing)
st.markdown("</div>", unsafe_allow_html=True)

error = ""
if send_clicked:
    error = validate_input(user_input)
    if not error:
        st.session_state.messages.append(
            {
                "id": len(st.session_state.messages) + 1,
                "type": "user",
                "content": user_input.strip(),
                "timestamp": timestamp(),
            }
        )
        st.session_state.is_typing = True
        st.rerun()

if st.session_state.is_typing:
    time.sleep(1.5)
    step = st.session_state.step
    if step < len(QUESTIONS):
        key = QUESTIONS[step][0]
        st.session_state.spec = update_spec(st.session_state.spec, key, st.session_state.messages[-1]["content"])
        query = example_query(key, st.session_state.messages[-1]["content"])
        results = retriever.search(query, top_k=3, repo="dsl-samples")
        patterns = build_patterns_message(results)
        st.session_state.messages.append(
            {
                "id": len(st.session_state.messages) + 1,
                "type": "ai",
                "content": patterns,
                "timestamp": timestamp(),
            }
        )
        st.session_state.step += 1
        if st.session_state.step < len(QUESTIONS):
            st.session_state.messages.append(
                {
                    "id": len(st.session_state.messages) + 1,
                    "type": "ai",
                    "content": QUESTIONS[st.session_state.step][1],
                    "timestamp": timestamp(),
                }
            )
        else:
            json_path, md_path = export_spec(st.session_state.spec, OUTPUT_DIR)
            st.session_state.messages.append(
                {
                    "id": len(st.session_state.messages) + 1,
                    "type": "system",
                    "content": f"Spec draft saved:<br>- {json_path}<br>- {md_path}",
                    "timestamp": timestamp(),
                }
            )
    st.session_state.is_typing = False
    st.rerun()

if error:
    st.caption(error)
