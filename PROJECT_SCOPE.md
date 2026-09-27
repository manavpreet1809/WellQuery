# WellQuery project scope

## Goal

Build a third-year university project that answers general health-information questions using a small document collection and shows the evidence behind each answer. The project is named WellQuery and builds on Manavpreet Singh's existing MediBot code. The GitHub repository is [manavpreet1809/WellQuery](https://github.com/manavpreet1809/WellQuery).

The project has no required Canadian or Alberta source focus. Sources will be selected for relevance, quality, and permission to reuse before ingestion.

## Core features

- A FastAPI backend and a simple web chat interface.
- A catalogue of 15–20 permitted health documents, with publisher, URL, and reuse terms.
- Document extraction, chunking, and storage with source metadata.
- Keyword, vector, and hybrid retrieval using reciprocal rank fusion.
- Question routing for medication, condition, and unsupported questions.
- One LLM provider, passage-level citations, and insufficient-evidence responses.
- An expandable evidence panel, response timing, and clear error states.
- Basic boundaries against personalized diagnosis and medication changes, plus fixed emergency guidance for tested phrases.
- Evaluation on 50–80 manually checked questions and a results dashboard.

These safeguards are prototype features, not validated clinical protections. The application provides general information, not medical advice, and does not claim affiliation with a health authority.

## Research question

Does question routing combined with hybrid retrieval improve answer quality compared with the original MediBot retrieval approach?

Compare the baseline, hybrid retrieval alone, and hybrid retrieval with routing using the same held-out questions. Report retrieval quality, routing accuracy, factual support from cited passages, and response latency. Keep threshold tuning questions separate from final evaluation questions. Record negative results as well as improvements.

## Delivery stages

1. **Foundation:** document scope and provenance, configure dependencies, and establish a working chat flow.
2. **Knowledge base:** catalogue sources, extract and chunk documents, and store embeddings.
3. **Smarter search:** implement keyword and vector modes, fuse results, and integrate routing.
4. **Reliable answers:** generate cited answers, handle insufficient evidence, and add basic safety boundaries.
5. **Interface:** improve chat states, show evidence and source links, and display timing and errors.
6. **Evaluation and demo:** verify questions, compare configurations, visualize results, and prepare documentation and a demo.

Use focused commits for working changes, with relevant tests alongside implementation. Detailed commit boundaries can be adjusted after reviewing the existing code.

## Out of scope for the first release

- Canadian-specific datasets or provincial statistics tools.
- MCP, multi-step autonomous agents, or multiple LLM providers.
- Terraform, event-driven ingestion, and mandatory cloud deployment.
- Patient records, personal health profiles, diagnosis, or treatment recommendations.
- Claims of clinical accuracy, regulatory approval, or production readiness.

Use fictional inputs for the demo and evaluation. A local demonstration is sufficient for the first release.

## Current status

Planning only. Manavpreet Singh has confirmed that MediBot is his own project and authorized using it as the foundation. No MediBot code or health documents have been imported. Source selection, implementation, and evaluation remain to be completed.
