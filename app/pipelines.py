"""The two pipelines, run over the same tickets.

DEMO-MODE HONESTY NOTE (also shown on the dashboard): no frontier model
is called anywhere in this demo. Pipeline step outputs are produced by
deterministic code, and the token counts are exact counts (tiktoken
cl100k when available) of the prompts and outputs actually produced.
What the demo proves is the *accounting shape* of the architecture:
how many tokens each design spends to reach the same answer. Costs use
illustrative frontier rates from ledger.py.

Pipeline A -- "agentic": five model-call steps per ticket
  triage -> policy lookup -> draft -> self-critique -> revise.
Pipeline B -- "token-minimal": deterministic classify, then a test gate
  (confidence threshold, required fields, known policy). Tests pass ->
  zero tokens. A gate failure spends exactly ONE frontier debug call.
"""

import time

from .classifier import CONFIDENCE_THRESHOLD, classify, gate_passes
from .ledger import frontier_cost
from .tickets import TICKETS
from .tokenizer import METHOD as TOKEN_METHOD, count

POLICIES = {
    "billing": "Billing issues: verify the charge in the billing system, then correct or reverse it.",
    "access": "Access issues: verify identity, then restore access via reset or unlock.",
    "delivery": "Delivery issues: trace the package, then replace or re-ship.",
    "refund": "Refund issues: confirm eligibility under the refund policy, then process.",
    "bug": "Bug reports: reproduce if possible, then escalate to engineering with steps.",
    "account": "Account requests: verify identity, then apply the requested change.",
}

DRAFTS = {
    "billing": "Thanks for flagging this. I've verified the charge and applied the correction to your billing account.",
    "access": "Thanks for reporting this. I've verified your identity and restored access to your account.",
    "delivery": "Thanks for letting us know. I've traced your package and arranged the next step for your delivery.",
    "refund": "Thanks for your patience. I've confirmed eligibility and processed your refund.",
    "bug": "Thanks for the report. I've logged this with engineering, including your reproduction steps.",
    "account": "Thanks for reaching out. I've verified your identity and applied the requested account change.",
}


def _step(prompt: str, completion: str):
    """One accounted model-call step: exact token counts of real strings."""
    in_tok = count(prompt)
    out_tok = count(completion)
    return in_tok, out_tok, frontier_cost(in_tok, out_tok)


def run_agentic(ticket):
    """Five model-call steps; the demo's stand-in for a token-heavy loop."""
    category, confidence, _ = classify(ticket["subject"], ticket["body"])
    steps = []
    total_in = total_out = 0
    total_cost = 0.0

    prompt = (f"You are a support agent. Triage this ticket.\n"
              f"Subject: {ticket['subject']}\nBody: {ticket['body']}")
    out = f"Category: {category}; Priority: {ticket['priority']}."
    i, o, c = _step(prompt, out)
    steps.append(("triage", i, o, c))
    total_in += i; total_out += o; total_cost += c

    prompt = (f"Find the policy for category '{category}'.\n"
              f"Ticket: {ticket['subject']}")
    out = POLICIES[category]
    i, o, c = _step(prompt, out)
    steps.append(("policy_lookup", i, o, c))
    total_in += i; total_out += o; total_cost += c

    prompt = (f"Draft a reply to this ticket.\nSubject: {ticket['subject']}\n"
              f"Body: {ticket['body']}\nPolicy: {POLICIES[category]}")
    out = DRAFTS[category]
    i, o, c = _step(prompt, out)
    steps.append(("draft", i, o, c))
    total_in += i; total_out += o; total_cost += c

    prompt = f"Critique this draft for policy compliance:\n{out}"
    out2 = "No issues found. Draft is consistent with policy."
    i, o, c = _step(prompt, out2)
    steps.append(("critique", i, o, c))
    total_in += i; total_out += o; total_cost += c

    prompt = f"Revise the draft based on this critique:\n{out2}\nDraft:\n{DRAFTS[category]}"
    out3 = DRAFTS[category]
    i, o, c = _step(prompt, out3)
    steps.append(("revise", i, o, c))
    total_in += i; total_out += o; total_cost += c

    return {
        "pipeline": "agentic",
        "predicted_category": category,
        "correct": category == ticket["category"],
        "input_tokens": total_in,
        "output_tokens": total_out,
        "cost_usd": round(total_cost, 6),
        "model_calls": len(steps),
        "debug_calls": 0,
        "gate_passed": None,
        "steps": steps,
    }


def run_token_minimal(ticket):
    """Deterministic classify + test gate; one debug call only on failure."""
    category, confidence, scores = classify(ticket["subject"], ticket["body"])
    tests = {
        "confidence_gate": gate_passes(confidence),
        "required_fields": bool(ticket["subject"] and ticket["body"]),
        "known_policy": category in POLICIES,
    }
    gate = all(tests.values())
    total_in = total_out = 0
    total_cost = 0.0
    debug_calls = 0
    steps = []

    if not gate:
        prompt = (f"A support ticket failed automated triage (confidence "
                  f"{confidence:.2f} below threshold {CONFIDENCE_THRESHOLD}). "
                  f"Resolve the category.\nSubject: {ticket['subject']}\n"
                  f"Body: {ticket['body']}\nScores: {scores}")
        out = (f"Resolved category: {category} (highest score; first-mentioned "
               f"signal). Confidence {confidence:.2f} was below the "
               f"{CONFIDENCE_THRESHOLD} gate, so this one debug call was spent.")
        i, o, c = _step(prompt, out)
        steps.append(("debug", i, o, c))
        total_in += i; total_out += o; total_cost += c
        debug_calls = 1

    return {
        "pipeline": "token_minimal",
        "predicted_category": category,
        "correct": category == ticket["category"],
        "input_tokens": total_in,
        "output_tokens": total_out,
        "cost_usd": round(total_cost, 6),
        "model_calls": debug_calls,
        "debug_calls": debug_calls,
        "gate_passed": gate,
        "confidence": round(confidence, 3),
        "tests": tests,
        "steps": steps,
    }


def run_comparison():
    """Run both pipelines over every ticket; returns rows + totals."""
    rows = []
    totals = {}
    for name, fn in (("agentic", run_agentic), ("token_minimal", run_token_minimal)):
        t0 = time.perf_counter()
        results = [fn(t) for t in TICKETS]
        ms = round((time.perf_counter() - t0) * 1000, 1)
        totals[name] = {
            "tickets": len(results),
            "correct": sum(1 for r in results if r["correct"]),
            "accuracy": round(sum(1 for r in results if r["correct"]) / len(results), 3),
            "input_tokens": sum(r["input_tokens"] for r in results),
            "output_tokens": sum(r["output_tokens"] for r in results),
            "total_tokens": sum(r["input_tokens"] + r["output_tokens"] for r in results),
            "cost_usd": round(sum(r["cost_usd"] for r in results), 6),
            "model_calls": sum(r["model_calls"] for r in results),
            "debug_calls": sum(r["debug_calls"] for r in results),
            "latency_ms": ms,
        }
        for ticket, r in zip(TICKETS, results):
            rows.append({
                "ticket_id": ticket["id"],
                "subject": ticket["subject"],
                "truth_category": ticket["category"],
                "pipeline": name,
                **{k: r[k] for k in ("predicted_category", "correct", "input_tokens",
                                     "output_tokens", "cost_usd", "model_calls",
                                     "debug_calls")},
            })
    a, b = totals["agentic"], totals["token_minimal"]
    savings = round(100 * (1 - b["cost_usd"] / a["cost_usd"]), 1) if a["cost_usd"] else 0.0
    return {
        "mode": "demo",
        "token_method": TOKEN_METHOD,
        "tickets": len(TICKETS),
        "totals": totals,
        "savings_pct": savings,
        "rows": rows,
    }
