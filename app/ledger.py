"""Cost ledger.

Rates are illustrative frontier-model prices (per 1M tokens), configurable
via env, and disclosed as such on the dashboard. The token-minimal
pipeline's deterministic steps cost $0 because they make no API call.
"""

import os

FRONTIER_INPUT_PER_1M = float(os.environ.get("FRONTIER_INPUT_PER_1M", "3.0"))
FRONTIER_OUTPUT_PER_1M = float(os.environ.get("FRONTIER_OUTPUT_PER_1M", "15.0"))


def frontier_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1_000_000 * FRONTIER_INPUT_PER_1M
            + output_tokens / 1_000_000 * FRONTIER_OUTPUT_PER_1M)
