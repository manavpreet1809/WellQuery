PYTHON := .venv/bin/python
LOCAL_PYTHON := .venv-local/bin/python
.PHONY: setup test run local check ingest index evaluate doctor smoke
setup:
	test -x $(PYTHON) || uv venv --python 3.12 .venv
	uv pip install --python $(PYTHON) -r requirements-llm.txt -r requirements-dev.txt
test:
	$(PYTHON) -m pytest -q
check: test
	git diff --check
run:
	$(PYTHON) -m uvicorn app.main:app --host 127.0.0.1 --port 8000
local:
	BACKEND_MODE=local $(LOCAL_PYTHON) -m uvicorn app.main:app --host 127.0.0.1 --port 8000
ingest:
	$(LOCAL_PYTHON) -m app.ingest --download
index:
	$(LOCAL_PYTHON) -m app.search --index --download-model
evaluate:
	$(LOCAL_PYTHON) -m evaluation.run --include-drafts
doctor:
	$(PYTHON) -m app.remote_check
smoke:
	$(PYTHON) -m app.remote_check --live
.PHONY: model-status model-smoke
model-status:
	$(LOCAL_PYTHON) -m app.synthesis
model-smoke:
	$(LOCAL_PYTHON) -m app.synthesis --live
OLLAMA_BIN := $(if $(wildcard data/models/ollama-runtime/ollama),data/models/ollama-runtime/ollama,ollama)
.PHONY: model-serve model-pull compare
model-serve:
	OLLAMA_MODELS="$(CURDIR)/data/models/ollama" OLLAMA_HOST=127.0.0.1:11434 $(OLLAMA_BIN) serve
model-pull:
	$(OLLAMA_BIN) pull qwen2.5:1.5b
compare:
	$(LOCAL_PYTHON) -m evaluation.compare --output evaluation/results/comparison-$$(date -u +%Y%m%dT%H%M%SZ)

.PHONY: setup-local local-doctor local-smoke
setup-local:
	test -x $(LOCAL_PYTHON) || uv venv --python 3.12 .venv-local
	uv pip install --python $(LOCAL_PYTHON) -r requirements-demo.lock
local-doctor:
	$(LOCAL_PYTHON) -m app.doctor
local-smoke:
	$(LOCAL_PYTHON) -m app.doctor --smoke
