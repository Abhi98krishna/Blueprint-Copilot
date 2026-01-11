.PHONY: api ui dev

api:
	. .venv/bin/activate && uvicorn app.api:app --reload --port 8001

ui:
	cd ui && npm install && npm run dev -- --host 127.0.0.1 --port 5173

dev:
	( . .venv/bin/activate && uvicorn app.api:app --reload --port 8001 ) & \
	( cd ui && npm install && npm run dev -- --host 127.0.0.1 --port 5173 )
