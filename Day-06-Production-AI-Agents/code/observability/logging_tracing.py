"""
Day 6 — Structured logging + tracing.

In production every agent run is traced end-to-end:
- Request received (request_id, user_id)
- Each LLM call (model, tokens, latency, cost)
- Each tool call (tool name, args, result, latency)
- Final response

Langfuse + OpenTelemetry are the usual pair.

Setup:
    uv sync
    cp .env.example .env
Run:
    uv run logging_tracing.py
"""
import logging
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

# Importing llm_config exports proxy env vars + gives us get_model().
sys.path.insert(0, str(Path(__file__).parent))
from llm_config import get_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("agent")


@dataclass
class RunTrace:
    request_id: str
    user_id: str
    events: list = field(default_factory=list)

    def event(self, kind: str, **payload):
        self.events.append({"kind": kind, **payload})
        log.info(kind, extra={"request_id": self.request_id, **payload})


@contextmanager
def trace_run(user_id: str):
    """Context manager that times and logs a full agent run."""
    t = RunTrace(request_id=f"req-{uuid.uuid4().hex[:8]}", user_id=user_id)
    start = time.perf_counter()
    try:
        yield t
    finally:
        t.event("run_complete", duration_ms=int((time.perf_counter() - start) * 1000))


if __name__ == "__main__":
    MODEL = get_model()
    with trace_run(user_id="u-42") as t:
        t.event("llm_call", model=MODEL, tokens_in=120, tokens_out=45, cost_usd=0.0003)
        t.event("tool_call", tool="search_docs", args={"q": "VPN"})
        t.event("tool_result", tool="search_docs", latency_ms=180)
        t.event("llm_call", model=MODEL, tokens_in=480, tokens_out=120, cost_usd=0.0012)

    print(f"\nCaptured {len(t.events)} events for {t.request_id}")
