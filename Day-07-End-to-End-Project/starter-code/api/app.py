"""
Day 7 — FastAPI service for the IT Support Multi-Agent System.

Setup:
    uv sync
    cp .env.example .env
Run:
    uv run --with uvicorn uvicorn app:app --reload --port 8000
Test:
    curl -X POST localhost:8000/support -H "Content-Type: application/json" \
         -d '{"user_id":"u-42","query":"VPN keeps dropping"}'
"""
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from langfuse import Langfuse
from pydantic import BaseModel

# Importing llm_config exports proxy env vars.
sys.path.insert(0, str(Path(__file__).parent.parent))
import llm_config  # noqa: F401

from graph import build_graph
from tools import PENDING_WRITES

app = FastAPI(title="IT Support Multi-Agent System")
graph = build_graph()
lf = Langfuse()
log = logging.getLogger("agent")
logging.basicConfig(level=logging.INFO)

# Per-user spend tracker (replace with Redis in production)
SPENT: dict[str, float] = {}
BUDGET_USD = 0.50


class SupportReq(BaseModel):
    user_id: str
    query: str


class SupportResp(BaseModel):
    trace_id: str
    answer: str
    citations: list[str]
    tool_calls: list[dict]
    tokens: dict
    cost_usd: float


@app.post("/support", response_model=SupportResp)
async def support(req: SupportReq):
    trace_id = f"lf-{datetime.utcnow():%Y%m%d}-{uuid.uuid4().hex[:8]}"
    trace = lf.trace(
        name="support_request",
        user_id=req.user_id,
        input=req.query,
        metadata={"trace_id": trace_id},
    )

    try:
        result = await graph.arun(req.query, user_id=req.user_id)

        cost = 0.012  # placeholder; compute from actual token usage
        SPENT[req.user_id] = SPENT.get(req.user_id, 0.0) + cost

        trace.update(output=result["answer"], usage={
            "input": result.get("tokens_in", 0),
            "output": result.get("tokens_out", 0),
        })

        return SupportResp(
            trace_id=trace_id,
            answer=result["answer"],
            citations=result.get("citations", []),
            tool_calls=result.get("tool_calls", []),
            tokens=result.get("tokens", {}),
            cost_usd=cost,
        )
    except Exception as e:
        trace.update(error=str(e))
        log.exception("agent_failed")
        raise HTTPException(500, "agent error")


@app.get("/approvals/pending")
def pending_approvals():
    """Human approver dashboard."""
    return {"pending": PENDING_WRITES}


@app.post("/approvals/{ticket_id}/approve")
def approve_ticket(ticket_id: str, approve: bool = True):
    """Approver UI calls this endpoint."""
    PENDING_WRITES[:] = [
        w for w in PENDING_WRITES if w["id"] != ticket_id
    ]
    return {"ticket_id": ticket_id, "approved": approve}


@app.get("/budget/{user_id}")
def get_budget(user_id: str):
    return {
        "user_id": user_id,
        "spent_usd": SPENT.get(user_id, 0.0),
        "limit_usd": BUDGET_USD,
    }
