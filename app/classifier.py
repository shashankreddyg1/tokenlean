"""Deterministic ticket classifier (the token-minimal pipeline's brain).

Pure keyword scoring over the ticket text -- no model call, no tokens.
`classify` returns the winning category, a confidence in [0, 1], and the
per-category scores so the test gate can inspect them.
"""

import re

KEYWORDS = {
    "billing": ["charged", "charge", "invoice", "payment", "billed",
                "subscription", "card", "deducted", "price"],
    "access": ["log in", "login", "password", "two-factor", "2fa",
               "locked out", "sso", "sign-in", "reset"],
    "delivery": ["delivered", "delivery", "tracking", "package",
                 "shipping", "delivery address", "arrived", "order"],
    "refund": ["refund", "cancelled", "damaged", "policy",
               "unused months", "cancellation"],
    "bug": ["crashes", "crash", "blank", "button", "safari",
            "does nothing", "no results", "search"],
    "account": ["email", "company name", "close my account",
                "delete"],
}

# Gate: a classification is trusted only when the winner is this confident.
CONFIDENCE_THRESHOLD = 0.6


def classify(subject: str, body: str):
    text = f"{subject} {body}".lower()
    scores = {}
    for category, words in KEYWORDS.items():
        # Word-boundary match: "crash" must not fire on "crashes".
        scores[category] = sum(
            2 if re.search(r"\b" + re.escape(w) + r"\b", text) else 0
            for w in words
        )
    total = sum(scores.values())
    winner = max(scores, key=scores.get)
    confidence = (scores[winner] / total) if total else 0.0
    return winner, confidence, scores


def gate_passes(confidence: float) -> bool:
    return confidence >= CONFIDENCE_THRESHOLD
