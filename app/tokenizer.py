"""Token counting.

Uses tiktoken's cl100k_base encoding when available (exact counts for the
prompts and outputs actually produced). Falls back to a whitespace
estimator, and reports which method was used so the ledger never implies
more precision than it has.
"""

try:
    import tiktoken

    _ENC = tiktoken.get_encoding("cl100k_base")
    METHOD = "tiktoken cl100k_base"
except Exception:  # pragma: no cover - environment without tiktoken
    _ENC = None
    METHOD = "whitespace estimate (tiktoken unavailable)"


def count(text: str) -> int:
    if _ENC is not None:
        return len(_ENC.encode(text))
    return max(1, len(text.split()))
