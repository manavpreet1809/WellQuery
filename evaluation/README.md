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

The emergency/injection examples are small and close to the phrase rules; they do not measure robust safety. Expand with independently written paraphrases, negations, ambiguous requests, and broader topics. Model loading affects the first vector latency; current timings are not a controlled benchmark. The default three-source collection and AI-derived labels limit generalization. The results dashboard is available at /evaluation and the demo script is in docs/DEMO.md. Human review is still required to close Day 9's verified-evaluation goal.

## Review tools

Export a review packet containing the current questions, labels, source passages, and blank decisions:

```sh
.venv/bin/python -m evaluation.review export --output evaluation/reviews/questions.json
```

As the human reviewer, inspect each question and its evidence. Set its `decision` to `approve` or `reject`, enter your name in `reviewer`, and explain your judgment in `notes`. Leave decisions null for unreviewed items. To correct a question or label, edit the source question dataset and export a fresh packet instead of changing the packet's snapshot. Then apply decisions to a **new** file:

```sh
.venv/bin/python -m evaluation.review apply --packet evaluation/reviews/questions.json --output evaluation/reviews/reviewed-questions.jsonl
.venv/bin/python -m evaluation.run --questions evaluation/reviews/reviewed-questions.jsonl
```

Application checks the exact dataset hash and question snapshots, rejects incomplete decisions and duplicate IDs, and never overwrites the original dataset or an existing output. This prevents accidental stale reviews, not falsified reviewer identity. Exporting a packet does not verify anything.

For answer review, copy a run's `answer_review.jsonl` into `evaluation/reviews/`. Enter `supported`, `unsupported`, or `uncertain` in `human_claim_support` for actual answers; use `not_applicable` for refusals. Enter `relevant`, `irrelevant`, or `uncertain` in `human_relevance`, and supply `reviewer`. Judge support against the quoted evidence and relevance against the actual question, not citation formatting alone.

```sh
.venv/bin/python -m evaluation.review summarize-answers evaluation/reviews/answer_review.jsonl
```

The summary reports counts and coverage; it never converts unreviewed answers into successes. A supported fraction of null means no answers have been reviewed. Review artifacts are ignored by Git unless deliberately published after inspection.

### Expanded-corpus challenge set

`challenge_questions.jsonl` contains 20 additional **unverified development** cases: kidney and medicine retrieval, unfamiliar emergency/personal-advice/injection phrasing, unrelated questions with topic overlap, and negation. It is separate from the original 60 questions and is not a held-out benchmark. Review its relevance and route labels before drawing conclusions.

```sh
.venv/bin/python -m evaluation.run --questions evaluation/challenge_questions.jsonl --include-drafts
```

Every new run also writes `failures.jsonl`: incomplete section retrieval per configuration, behavior mismatches, and route mismatches. Counts are events, not unique failed questions. A retrieval-only run has no behavior judgments. Human answer-review fields remain blank.

The October 7 draft run against 15 sources/201 chunks produced 7 retrieval-miss events, 6 behavior mismatches, and 9 route mismatches. It missed unfamiliar urgent phrasing, personal-dose and injection requests, answered a laptop question containing “diabetes,” and falsely blocked a negated chest-pain question. These are known prototype limitations. No rule changes were fitted to this set; future improvements need separate evaluation cases. Historical three-source scores are not expanded-corpus scores.
