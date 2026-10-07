PYTHON := .venv/bin/python
.PHONY: setup test run local check ingest index evaluate doctor smoke
setup:
	uv venv --python 3.12 .venv
	uv pip install --python $(PYTHON) -r requirements-demo.lock
test:
	$(PYTHON) -m pytest -q
check: test
	git diff --check
run:
	$(PYTHON) -m uvicorn app.main:app --host 127.0.0.1 --port 8000
local:
	BACKEND_MODE=local $(PYTHON) -m uvicorn app.main:app --host 127.0.0.1 --port 8000
ingest:
	$(PYTHON) -m app.ingest --download
index:
	$(PYTHON) -m app.search --index --download-model
evaluate:
	$(PYTHON) -m evaluation.run --include-drafts
doctor:
	$(PYTHON) -m app.doctor
smoke:
	$(PYTHON) -m app.doctor --smoke
.PHONY: model-status model-smoke
model-status:
	$(PYTHON) -m app.synthesis
model-smoke:
	$(PYTHON) -m app.synthesis --live
OLLAMA_BIN := $(if $(wildcard data/models/ollama-runtime/ollama),data/models/ollama-runtime/ollama,ollama)
.PHONY: model-serve model-pull compare
model-serve:
	OLLAMA_MODELS="$(CURDIR)/data/models/ollama" OLLAMA_HOST=127.0.0.1:11434 $(OLLAMA_BIN) serve
model-pull:
	$(OLLAMA_BIN) pull qwen2.5:1.5b
compare:
	$(PYTHON) -m evaluation.compare --output evaluation/results/comparison-$$(date -u +%Y%m%dT%H%M%SZ)
