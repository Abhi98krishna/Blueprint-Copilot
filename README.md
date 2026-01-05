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
