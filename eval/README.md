# RAG Evaluation Harness

Measures retrieval and generation quality of the Finverse Research Copilot so
pipeline changes (chunking, embeddings, reranking) can be proven to help before
shipping. Without this, every "improvement" is faith-based.

## Run

```bash
# Retrieval metrics only — fast, deterministic, no API key
python -m eval.run_eval

# + generation metrics (answer correctness, citation validity, faithfulness)
python -m eval.run_eval --gen

python -m eval.run_eval --k 8 --limit 5 --json   # options

# Regression gate (CI-friendly; retrieval only)
pytest eval/test_rag_gate.py -v
```

## Metrics

| Metric | What it measures | Needs LLM |
| --- | --- | --- |
| Recall@k (hit rate) | top-k contains a chunk with the gold evidence | no |
| MRR | 1 / rank of first relevant chunk | no |
| NDCG@k | rank-discounted relevance | no |
| Answer correctness | expected facts present in the answer | generation |
| Citation validity | every `[n]` points to a real source | generation |
| Faithfulness | LLM judge: answer grounded in context | yes (judge) |

## Golden set (`golden_set.jsonl`)

One JSON object per line:

```json
{"id": "tcs-rev-fy26",
 "question": "What was TCS consolidated revenue in fiscal 2026?",
 "symbol": "TCS",
 "answer_contains": ["267,021"],
 "evidence_terms": ["267,021"]}
```

- `evidence_terms` — a retrieved chunk counts as relevant if it contains any of
  these (case-insensitive). Drives the retrieval metrics.
- `answer_contains` — facts the generated answer should include (correctness).
  Leave `[]` for qualitative questions.

### Growing toward 50–100 questions

The seed set is grounded in the currently-indexed corpus (TCS annual report +
Acme test doc). To scale it truthfully:

1. Add questions whose answers you can verify against an indexed chunk.
2. Keep a mix: precise figures, qualitative (risks/strategy), and multi-fact.
3. Cover every `symbol`/`doc_type` you expect users to query.
4. Never assert a fact you haven't confirmed is in the corpus — a wrong gold
   label silently corrupts the metric.
