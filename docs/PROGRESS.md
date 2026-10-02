# WellQuery commit progress

## Day 2 — original MediBot baseline

Imported Manavpreet Singh's `app`, `llm`, `templates`, `static`, and original requirements from the supplied MediBot folder. `medibot-baseline.json` records SHA-256 hashes of the imported files so later changes can be distinguished from the original work.

Databricks notebooks, training helpers, caches, and empty deployment stubs were not imported. The original external serving endpoints remain dependencies of the baseline. No model weights, third-party health documents, or secrets were imported.

Validation: Python files parse successfully; imported files were checked for common GitHub, Hugging Face, and Databricks token patterns. This is a baseline snapshot, not a claim that live Databricks inference has been tested. The next commit will address startup configuration, missing web dependencies, and failure handling.

## Day 3 — stabilize the chat flow

Added credential-free startup, explicit scripted demo mode, a single shared classify/retrieve/answer pipeline, bounded request parameters, rejection of missing full-text evidence, generic upstream errors, and offline dependency injection tests. Removed external UI assets and HTML string interpolation; both user and model messages are rendered as text. Added loading/error handling, local setup instructions, and separate optional model dependencies.

Validation: 12 offline API tests passed, including the complete pipeline with injected classifier, retriever, and generator. No real health-answer quality or live Databricks/model inference is claimed. The small frontend change is for baseline operation; the evidence panel and visual polish remain later work.
