"""TokenLean demo API for Vercel serverless.

The deterministic pipelines in app/ need no broker, database, or API key,
so the serverless function runs the exact same code as the local backend.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402
