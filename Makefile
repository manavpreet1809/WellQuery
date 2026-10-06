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
