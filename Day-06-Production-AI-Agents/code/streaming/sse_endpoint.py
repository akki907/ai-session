"""
Day 6 — SSE streaming endpoint.

Setup:
    uv sync
    cp .env.example .env
Run:
    uv run --with uvicorn uvicorn sse_endpoint:app --reload --port 8001
Test:
    curl -N localhost:8001/agent/stream?q=hello
"""
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

# Importing llm_config exports proxy env vars + gives us get_client/get_model.
sys.path.insert(0, str(Path(__file__).parent))
from llm_config import get_client, get_model

app = FastAPI()
client = get_client()
MODEL = get_model()

SYSTEM = "You are a helpful assistant."


async def stream(q: str):
    stream_iter = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM},
                 {"role": "user", "content": q}],
        stream=True,
    )
    for chunk in stream_iter:
        if chunk.choices and chunk.choices[0].delta.content:
            yield f"data: {chunk.choices[0].delta.content}\n\n"
    yield "data: [DONE]\n\n"


@app.get("/agent/stream")
async def agent_stream(q: str):
    return StreamingResponse(stream(q), media_type="text/event-stream")
