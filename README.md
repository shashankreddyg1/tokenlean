# TokenLean

**Token-minimal support automation — the same tickets, two architectures, one ledger.**

The naive way to build an "AI agent" is a token-heavy loop: call a frontier
model at every step. TokenLean shows the alternative from the
[token-minimizing](https://www.instagram.com/reel/DfFrNLbyt-5/) idea:
deterministic code does the work, tests decide when a token gets spent,
and a small model handles only the narrow step that needs language.

## What it does

25 labeled support tickets run through two pipelines side by side:

- **Agentic (baseline):** 5 model-call steps per ticket — triage, policy
  lookup, draft, self-critique, revise.
- **Token-minimal:** deterministic keyword classification, then a test gate
  (confidence threshold, required fields, known policy). Tests pass → **zero
  tokens**. A gate failure spends exactly **one** frontier debug call.

A live ledger records input/output tokens and cost per ticket for both
pipelines, plus accuracy against the ground-truth labels.

## Measured results (25 tickets, demo run)

| | Agentic | Token-minimal |
|---|---|---|
| Accuracy | 1.000 | 1.000 |
| Total tokens | 5,967 | 257 |
| Cost (illustrative frontier rates) | $0.038241 | $0.001611 |
| Model calls | 125 | 2 |
| Debug calls | 0 | 2 (tickets 24, 25 — deliberately ambiguous) |

**Cost savings: 95.8% at identical accuracy.**

## Honesty note (demo mode)

No frontier model is called anywhere in this demo. Step outputs are
produced by deterministic code, and the token counts are exact counts
(tiktoken `cl100k_base`) of the prompts and outputs actually produced.
Costs use illustrative frontier rates ($3/1M input, $15/1M output),
configurable via `FRONTIER_INPUT_PER_1M` / `FRONTIER_OUTPUT_PER_1M`.
What the demo proves is the *accounting shape* of the architecture:
how many tokens each design spends to reach the same answer.

## Run locally

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest tests/ -q
.venv/bin/python -m uvicorn app.main:app --port 8125
# GET /health, /tickets, /compare
```

## Live demo

Dashboard: https://shashankreddyg1.github.io/tokenlean/
API: see `docs/index.html` (`API_BASE`; Vercel serverless, same code as `app/`).

## Stack

Python + FastAPI. No database, no API key, no broker — the whole pipeline
is deterministic, which is the point.
