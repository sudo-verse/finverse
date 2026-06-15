"""RAG evaluation harness for the Finverse Research Copilot.

Runs a golden question set through the live retrieval (and optionally
generation) pipeline and reports the metrics that actually predict answer
quality, so any change to chunking / embeddings / retrieval can be proven to
help or hurt before it ships.

Retrieval metrics (deterministic, no LLM, always run):
  - Recall@k (hit rate) ... did top-k contain a chunk with the gold evidence?
  - MRR ................... 1 / rank of the first relevant chunk
  - NDCG@k ............... rank-discounted gain of relevant chunks

Generation metrics (need GEMINI_API_KEY, run with --gen):
  - Answer correctness ... fraction of expected facts present in the answer
  - Citation validity .... every [n] in the answer points to a real source
  - Faithfulness ......... LLM judge: is the answer grounded in the context?

Usage:
    python -m eval.run_eval                 # retrieval only
    python -m eval.run_eval --gen           # + generation metrics
    python -m eval.run_eval --k 8 --limit 5
"""

import argparse
import json
import math
import os
import re
import sys

from app.genai import research

GOLDEN = os.path.join(os.path.dirname(__file__), "golden_set.jsonl")
_CITE_RE = re.compile(r"\[(\d+)\]")


def _load(path: str) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def _is_relevant(text: str, evidence_terms: list[str]) -> bool:
    low = (text or "").lower()
    return any(term.lower() in low for term in evidence_terms)


def _ndcg(rels: list[int]) -> float:
    """Binary NDCG over a ranked list of 0/1 relevance flags."""
    dcg = sum(r / math.log2(i + 2) for i, r in enumerate(rels))
    n_rel = sum(rels)
    idcg = sum(1 / math.log2(i + 2) for i in range(n_rel))
    return dcg / idcg if idcg else 0.0


# --------------------------------------------------------------- generation
def _judge_faithfulness(question: str, answer: str, context: str) -> float | None:
    from app.genai import gemini_client

    if not gemini_client.is_configured():
        return None
    prompt = (
        f"Question: {question}\n\nCONTEXT:\n{context[:8000]}\n\n"
        f"ANSWER:\n{answer[:3000]}\n\n"
        "Rate from 0 to 100 how fully the ANSWER is supported by the CONTEXT "
        "(100 = every claim is grounded, 0 = unsupported/hallucinated). "
        "Reply with ONLY the integer."
    )
    try:
        raw = gemini_client.generate_text(
            prompt, system_instruction="You are a strict RAG faithfulness judge."
        )
        m = re.search(r"\d{1,3}", raw or "")
        return min(int(m.group(0)), 100) / 100 if m else None
    except Exception:
        return None


def _citation_validity(answer: str, n_sources: int) -> float | None:
    cites = [int(n) for n in _CITE_RE.findall(answer)]
    if not cites:
        return None  # no citations to validate
    valid = sum(1 for c in cites if 1 <= c <= n_sources)
    return valid / len(cites)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=6, help="top-k chunks to retrieve")
    ap.add_argument("--gen", action="store_true", help="also score generation")
    ap.add_argument("--limit", type=int, default=None, help="first N questions")
    ap.add_argument("--json", action="store_true", help="emit JSON summary")
    args = ap.parse_args()

    items = _load(GOLDEN)
    if args.limit:
        items = items[: args.limit]

    recalls, mrrs, ndcgs = [], [], []
    corrects, citations, faiths = [], [], []
    rows = []

    for it in items:
        sources = research.retrieve(it["question"], symbol=it.get("symbol"), k=args.k)
        rels = [1 if _is_relevant(s.get("text", ""), it["evidence_terms"]) else 0
                for s in sources]
        hit = 1.0 if any(rels) else 0.0
        first = next((i + 1 for i, r in enumerate(rels) if r), None)
        mrr = 1.0 / first if first else 0.0
        ndcg = _ndcg(rels)
        recalls.append(hit); mrrs.append(mrr); ndcgs.append(ndcg)

        row = {"id": it["id"], "recall": hit, "mrr": round(mrr, 3),
               "ndcg": round(ndcg, 3), "hits": sum(rels), "k": len(sources)}

        if args.gen:
            srcs, gen = research.research_answer(it["question"], symbol=it.get("symbol"), k=args.k)
            answer = "".join(gen)
            exp = it.get("answer_contains") or []
            if exp:
                c = sum(1 for e in exp if e.lower() in answer.lower()) / len(exp)
                corrects.append(c); row["correct"] = round(c, 2)
            cv = _citation_validity(answer, len(srcs))
            if cv is not None:
                citations.append(cv); row["cite_ok"] = round(cv, 2)
            ctx = "\n\n".join(s.get("text", "") for s in srcs)
            f = _judge_faithfulness(it["question"], answer, ctx)
            if f is not None:
                faiths.append(f); row["faith"] = round(f, 2)
        rows.append(row)

    def mean(xs):
        return round(sum(xs) / len(xs), 3) if xs else None

    summary = {
        "n": len(items), "k": args.k,
        "recall@k": mean(recalls), "mrr": mean(mrrs), "ndcg@k": mean(ndcgs),
    }
    if args.gen:
        summary.update({"answer_correctness": mean(corrects),
                        "citation_validity": mean(citations),
                        "faithfulness": mean(faiths)})

    if args.json:
        print(json.dumps({"summary": summary, "rows": rows}, indent=2))
    else:
        print(f"\n{'id':<18} recall  mrr   ndcg  hits/k" + ("  correct cite  faith" if args.gen else ""))
        print("-" * (50 if not args.gen else 74))
        for r in rows:
            line = f"{r['id']:<18} {r['recall']:>5.0f}  {r['mrr']:>4.2f}  {r['ndcg']:>4.2f}  {r['hits']}/{r['k']}"
            if args.gen:
                line += f"   {r.get('correct','—'):>5}  {r.get('cite_ok','—'):>4}  {r.get('faith','—'):>4}"
            print(line)
        print("-" * (50 if not args.gen else 74))
        print("SUMMARY:", json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
