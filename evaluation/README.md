# Evaluation and human review

The initial dataset contains **60 AI-drafted, unverified questions**: 40 factual/paraphrase questions in 20 topic groups, plus five each for emergency redirection, personal-advice refusal, injection, and absent-corpus topics. No question or answer has been marked human-verified. The three-source corpus covers diabetes only.

## Run

```sh
# Requires ingested documents, the vector index, and requirements-search.txt
.venv/bin/python -m evaluation.run --include-drafts
# Defaults to human-verified questions; exits clearly if there are none:
.venv/bin/python -m evaluation.run
```

Results are timestamped under ignored `evaluation/results/`. The runner never overwrites a previous result directory. It writes:

- `summary.json`: dataset status, corpus/model/code provenance, per-split configuration results, rule-routing accuracy, and refusal behavior by category.
- `retrieval.csv`: per-question Recall@5, reciprocal rank at 5, configuration, split, and latency.
- `answer_review.jsonl`: local **excerpt** answers, evidence, exact-quote validity, and empty fields for human claim-support/relevance review. This does not evaluate Ollama synthesis.

Retrieval compares keyword BM25, vector cosine, hybrid RRF, and hybrid with local routing. Relevant units are exact document/section pairs; multiple overlapping chunks from the same section count only once. MRR@5 measures the first relevant result. A relevant section label may be incomplete or wrong until reviewed. Behaviour match means an answer/refusal category matched its label; it does not mean an answer is correct. Quote validity checks exact text membership, not entailment.

## Human review procedure

1. Open each question's original source and verify its relevant sections or expected refusal. Correct the route label based on intended topic, not the model's prediction.
2. Keep related paraphrases in the same group and split. Development questions are for debugging. Reserve test questions for final reporting; once used to guide changes, treat that test set as development and prepare a new held-out set.
3. Only after reviewing a question, set `verified` to `true` and record yourself in `reviewer`. Keep uncertain items unverified. Do not use a script to mark all questions verified.
4. Separately review each exported answer against its cited passage and the question. Fill `human_claim_support`, `human_relevance`, and `reviewer` in a saved copy of the answer-review file. The runner leaves them null and does not calculate factual accuracy from citation syntax.
5. Rerun without `--include-drafts` for question-verified results. Human-verified questions alone do not establish answer accuracy or clinical safety.

## Initial development observations — not headline metrics

The first 60-question run completed on October 4, 2026 (America/Edmonton). Its draft test split had 14 factual questions: hybrid retrieval found labeled sections within five results for all 14, while hybrid plus routing did so for 13. This is evidence of a development issue, not a validated quality estimate. The narrow condition-only corpus makes medication routing particularly brittle. No routing improvement is claimed.

The emergency/injection examples are small and close to the phrase rules; they do not measure robust safety. Expand with independently written paraphrases, negations, ambiguous requests, and broader topics. Model loading affects the first vector latency; current timings are not a controlled benchmark. The default three-source collection and AI-derived labels limit generalization. The final dashboard and presentation remain Day 10; human review is still required to close Day 9's verified-evaluation goal.
