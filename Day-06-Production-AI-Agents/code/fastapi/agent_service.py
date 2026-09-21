"""
Day 6 — FastAPI agent service with tracing, retry, and budget.

Setup:
    uv sync
    cp .env.example .env
Run:
    uv run --with uvicorn uvicorn agent_service:app --reload --port 8000
"""
import logging
import sys
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from langfuse import Langfuse
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

# Importing llm_config exports proxy env vars + gives us get_client/get_model.
sys.path.insert(0, str(Path(__file__).parent))
from llm_config import get_client, get_model

app = FastAPI(title="Enterprise Agent API")
client = get_client()
MODEL = get_model()
lf = Langfuse()
log = logging.getLogger("agent")
logging.basicConfig(level=logging.INFO)


# --- In-memory budget store (replace with Redis in production) ---
SPENT: dict[str, float] = {}
BUDGET_LIMIT_USD = 0.50


class RunReq(BaseModel):
    user_id: str
    query: str


class RunResp(BaseModel):
    answer: str
    tokens_in: int
    tokens_out: int
    cost_usd: float


SYSTEM = "You are an enterprise IT support agent."


@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
def llm_call(messages):
    return client.chat.completions.create(model=MODEL, messages=messages)


def run_agent(req: RunReq) -> RunResp:
    spent = SPENT.get(req.user_id, 0.0)
    if spent > BUDGET_LIMIT_USD:
        raise HTTPException(429, f"user {req.user_id} over budget")

    trace = lf.trace(
        name="agent_run",
        user_id=req.user_id,
        input=req.query,
        timestamp=datetime.utcnow(),
    )

    try:
        resp = llm_call([
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": req.query},
        ])
        msg = resp.choices[0].message
        usage = resp.usage

        # Pricing estimate (input $0.15/1M, output $0.60/1M for gpt-4o-mini;
        # bifrost proxy may differ — adjust per provider).
        cost = (usage.prompt_tokens * 0.15 + usage.completion_tokens * 0.60) / 1_000_000
        SPENT[req.user_id] = spent + cost

        trace.update(output=msg.content, usage={
            "input": usage.prompt_tokens,
            "output": usage.completion_tokens,
        })
        log.info("agent_done", extra={
            "user_id": req.user_id,
            "model": resp.model,
            "tokens_in": usage.prompt_tokens,
            "tokens_out": usage.completion_tokens,
            "cost_usd": cost,
        })

        return RunResp(
            answer=msg.content or "",
            tokens_in=usage.prompt_tokens,
            tokens_out=usage.completion_tokens,
            cost_usd=cost,
        )
    except Exception as e:
        trace.update(error=str(e))
        log.exception("agent_failed")
        raise HTTPException(500, "agent error")


@app.post("/agent/run", response_model=RunResp)
def agent_run(req: RunReq):
    return run_agent(req)


@app.get("/agent/budget/{user_id}")
def get_budget(user_id: str):
    return {"user_id": user_id, "spent_usd": SPENT.get(user_id, 0.0), "limit_usd": BUDGET_LIMIT_USD}
