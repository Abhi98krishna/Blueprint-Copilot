# Dev Workflow

## Setup

```bash
cd /Users/abkrishna/Documents/Projects/nutanix-dsl-study
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Run API

```bash
make api
```

API defaults to `http://127.0.0.1:8001`.

## Run UI

```bash
make ui
```

UI defaults to `http://127.0.0.1:5173`.

## Run both

```bash
make dev
```

## Quick API checks

```bash
curl -s http://127.0.0.1:8001/
curl -s -X POST http://127.0.0.1:8001/session
curl -s -X POST http://127.0.0.1:8001/chat \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"<SESSION_ID>","message":"A basic web app"}'
curl -s -X POST http://127.0.0.1:8001/compare \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"<SESSION_ID>","message":"A basic web app","variant":{"confidence_range":"Balanced","evidence_source":"Product artifacts","risk_tolerance":"Pragmatic","expression_style":"Concrete"}}'
```

## Troubleshooting

- 404 on `/` is fine; use `/docs` for interactive API docs.
- Address already in use -> choose a different port (e.g., `--port 8002`).
- ModuleNotFoundError -> run `pip install -r requirements.txt` inside the venv.
