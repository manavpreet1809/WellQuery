.PHONY: test run check
test:
	.venv/bin/python -m pytest -q
check: test
	git diff --check
run:
	.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
