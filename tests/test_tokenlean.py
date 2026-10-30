"""Tests for TokenLean. All assertions are about measured behavior:
accuracy on the fixed labeled set, exact ledger math, gate behavior,
and determinism across runs.
"""

from fastapi.testclient import TestClient

from app.main import app

from app.classifier import classify
from app.ledger import FRONTIER_INPUT_PER_1M, FRONTIER_OUTPUT_PER_1M, frontier_cost

client = TestClient(app)
from app.pipelines import run_agentic, run_comparison, run_token_minimal
from app.tickets import TICKETS
from app.tokenizer import count


def test_classifier_accuracy_on_labeled_set():
    correct = sum(
        1 for t in TICKETS
        if classify(t["subject"], t["body"])[0] == t["category"]
    )
    # Ambiguous tickets tie-break to the first-mentioned category, which
    # matches their ground truth by construction.
    assert correct == len(TICKETS)


def test_gate_fires_only_on_ambiguous_tickets():
    failing = [
        t["id"] for t in TICKETS
        if not run_token_minimal(t)["gate_passed"]
    ]
    assert failing == [24, 25]
    for t in TICKETS:
        r = run_token_minimal(t)
        assert r["debug_calls"] == (0 if r["gate_passed"] else 1)


def test_ledger_math():
    assert frontier_cost(1_000_000, 0) == FRONTIER_INPUT_PER_1M
    assert frontier_cost(0, 1_000_000) == FRONTIER_OUTPUT_PER_1M
    r = run_agentic(TICKETS[0])
    assert r["cost_usd"] == round(frontier_cost(r["input_tokens"], r["output_tokens"]), 6)
    assert r["model_calls"] == 5


def test_tokenizer_deterministic():
    assert count("hello world") > 0
    assert count("hello world") == count("hello world")


def test_comparison_deterministic_and_minimal_wins_on_cost():
    a = run_comparison()
    b = run_comparison()
    # Totals must match except wall-clock latency, which legitimately varies.
    for totals in (a["totals"], b["totals"]):
        for v in totals.values():
            v.pop("latency_ms")
    assert a["totals"] == b["totals"]
    assert a["totals"]["token_minimal"]["cost_usd"] < a["totals"]["agentic"]["cost_usd"]
    assert a["totals"]["token_minimal"]["accuracy"] == a["totals"]["agentic"]["accuracy"]
    assert a["savings_pct"] > 90


def test_api_endpoints():
    assert client.get("/health").json()["status"] == "ok"
    data = client.get("/compare").json()
    assert data["tickets"] == len(TICKETS)
    assert len(data["rows"]) == 2 * len(TICKETS)
    assert data["totals"]["token_minimal"]["debug_calls"] == 2
