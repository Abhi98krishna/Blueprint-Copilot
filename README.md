# Blueprint Buddy (Nutanix DSL Study)

Local chatbot for exploring Nutanix Calm/NCM Self-Service DSL code and sample blueprints. It indexes local clones of the DSL repo and sample blueprints, then answers with citations grounded in those files.

## Quick start

```bash
cd /Users/abkrishna/Documents/Projects/nutanix-dsl-study
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.cli
```

Optional web UI:

```bash
streamlit run app/web.py
```

## Local API (for Vite UI)

Run the API:

```bash
uvicorn app.api:app --reload --port 8001
```

Run Vite UI + API together:

```bash
# Terminal 1
uvicorn app.api:app --reload --port 8001

# Terminal 2
cd ui
npm install
npm run dev
```

Quick curl test:

```bash
curl -s -X POST http://127.0.0.1:8001/session
curl -s -X POST http://127.0.0.1:8001/chat \\
  -H 'Content-Type: application/json' \\
  -d '{"session_id":"<SESSION_ID>","message":"A basic web app"}'
```

Compare endpoint example:

```bash
curl -s -X POST http://127.0.0.1:8001/compare \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"<SESSION_ID>","message":"A basic web app","variant":{"confidence_range":"Balanced","evidence_source":"Product artifacts","risk_tolerance":"Pragmatic","expression_style":"Concrete"}}'
```

## Response Quality Lab

- In the Vite UI, each assistant message includes a **Compare responses** button.
- Clicking it opens the Response Quality Lab drawer on the right.
- The Lab requests two variants for the last user message via `POST /compare`.
- Changing a parameter reruns only that variant and does not affect the main session.
- Presets are stored in `localStorage` under `bp_lab_presets`.

## Data sources

- `data/calm-dsl`
- `data/dsl-samples`

The index is written to `index/index.jsonl` with chunk metadata.

## CLI usage

- Guide mode (default):

```bash
python -m app.cli
```

- Ask mode:

```bash
python -m app.cli --mode ask
```

- Rebuild index:

```bash
python -m app.cli --reindex
```

## Guardrails

- Responses include at least one citation in the form `file_path:Lx-Ly`.
- If retrieval confidence is low, the bot responds:
  `I can't support that from the DSL/blueprint code I indexed.`
- The only hardcoded knowledge is a minimal definition of a blueprint; any DSL behavior claims must be grounded in indexed code/samples.

## Outputs

Guide mode produces a spec draft in:

- `output/spec_<timestamp>.json`
- `output/spec_<timestamp>.md`
