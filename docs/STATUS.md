# Completion checklist

## Implemented and tested

- [x] Imported original MediBot baseline with provenance.
- [x] Local API startup, request validation, and failure handling.
- [x] Fifteen-source catalogue, section extraction, chunking, and SQLite persistence.
- [x] Keyword/vector/hybrid retrieval and local routing baseline.
- [x] Cited excerpt answers and prototype safeguards.
- [x] Optional Ollama adapter tested using injected model responses and HTTP fixtures; readiness/live-probe commands available.
- [x] Evidence panel verified in a real browser.
- [x] Evaluation runner and 80 explicitly draft questions and per-case failure exports.
- [x] Results dashboard with draft status and provenance.
- [x] Human-review packet tools; no automatic verification.
- [x] Dependency snapshot, readiness/smoke commands, architecture, and demo script.

## Outstanding before a finished submission

- [ ] Human review of the question labels and exported answer support/relevance.
- [ ] A fresh held-out set if the current test split is used to guide further changes.
- [x] Expand to the planned minimum: 15 catalogued documents across diabetes, kidney health, and medication information.
- [ ] Live Ollama validation if synthesis is included in the presentation.
- [ ] Record and review a demo video and align the final report with the course rubric.

The implemented tooling is not evidence of clinical safety. The project remains a local student prototype with narrow topic coverage; completed commits do not make all acceptance goals complete.

The expanded-corpus challenge run exposed 6 behavior mismatches out of 20 unverified development cases, including emergency paraphrases and negation. These known rule limitations remain open.
