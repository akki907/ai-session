# 7-Day AI Agents Training Program

A complete, hands-on training program covering LLM fundamentals through to a production-ready multi-agent system. **No git operations are run by this program — files only.**

## What's Here

| Day | Topic | Project |
|-----|-------|---------|
| [Day 1](Day-01-GenAI-LLM-Fundamentals/) | Generative AI + LLM Fundamentals | Enterprise IT Support Assistant |
| [Day 2](Day-02-AI-Agents-and-Architecture/) | AI Agents & Architecture | IT Support Agent (tools + HITL) |
| [Day 3](Day-03-RAG/) | RAG & Knowledge-Based Agents | Enterprise Policy Agent |
| [Day 4](Day-04-Agent-Frameworks-and-MCP/) | Agent Frameworks & MCP | Research Agent |
| [Day 5](Day-05-Multi-Agent-Systems/) | Multi-Agent Systems | Planner/Worker/Supervisor/Reviewer |
| [Day 6](Day-06-Production-AI-Agents/) | Production AI Agents | Production Enterprise Agent |
| [Day 7](Day-07-End-to-End-Project/) | End-to-End Enterprise Agent | IT Support Multi-Agent System |

## Per-Day Contents

Each day folder contains (where applicable):

| File | Purpose |
|------|---------|
| `presentation.html` | 45-minute slide deck (open in any browser) |
| `notes.md` | Detailed explanations — the "why" behind concepts |
| `hands-on.md` | 15-minute build session instructions |
| `project.md` | Project brief |
| `resources.md` | Curated links |
| `code/` | Starter code (Python) |

## Presentation Controls

Every `presentation.html` is keyboard-driven:

| Key | Action |
|-----|--------|
| `→` / `Space` | Next slide |
| `←` | Previous slide |
| `Home` | First slide |
| `End` | Last slide |
| `F` | Fullscreen toggle |
| `Esc` | Exit fullscreen |

There is also a progress bar at the top and a slide counter in the footer.

## Quick Start

Every code directory is self-contained and uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# 0. Install uv (one time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 1. Pick a day and read its presentation
open Day-01-GenAI-LLM-Fundamentals/presentation.html

# 2. Run the Day 1 demo
cd Day-01-GenAI-LLM-Fundamentals/code/basic-llm
uv sync
cp .env.example .env          # then edit .env with your OPENAI_API_KEY
uv run basic_llm_call.py

# 3. Day 7 capstone (full stack: API + RAG + multi-agent)
cd Day-07-End-to-End-Project/starter-code
uv sync
cp .env.example .env
uv run python rag/ingest.py --dir data
uv run --with uvicorn uvicorn api.app:app --reload --port 8000
```

`uv sync` reads `pyproject.toml` and creates an isolated `.venv/` per code directory.
`uv run <cmd>` automatically activates the venv — no `source .venv/bin/activate` needed.

## Project Progression

The capstone is an **Enterprise IT Support Multi-Agent System** that
grows across the week:

```
Day 1   LLM calls + structured output (IT Support Assistant)
Day 2   Tool-calling agent + guardrails + HITL gate on writes
Day 3   Add RAG: search enterprise docs, ground answers, cite sources
Day 4   Wire LangGraph + CrewAI + MCP for orchestration
Day 5   Split into Planner / Knowledge / Ticket / Escalation / Reviewer agents
Day 6   Wrap in FastAPI + SSE + tracing + budget cap
Day 7   Ship end-to-end (5 agents, 4 tools, RAG, HITL, eval)
```

By Day 7 the same `it-support-agent` concept from Day 1 has become a
production-grade multi-agent system.

## Tech Stack

- **Language:** Python 3.11+
- **LLM:** OpenAI gpt-4o / gpt-4o-mini (Azure OpenAI works too)
- **Frameworks:** LangChain · LangGraph · CrewAI · MCP
- **Vector DB:** Chroma (workshop) · pgvector (production)
- **API:** FastAPI + SSE streaming
- **Observability:** Langfuse + OpenTelemetry
- **Durability:** Temporal (production)
- **Testing:** pytest

## Learning Outcomes

By end of Day 7, participants can:

- Build a tool-calling agent from scratch
- Add RAG, guardrails, HITL, memory, multi-agent routing
- Deploy as a production API with streaming, tracing, and budgets
- Read and modify an agent YAML spec
- Evaluate an agent (offline + online)
- Identify and fix common mistakes (injection, runaway cost, no HITL, etc.)

## Repository Structure

```
ai-agents-training/
├── README.md
├── Day-01-GenAI-LLM-Fundamentals/
│   ├── presentation.html
│   ├── notes.md
│   ├── hands-on.md
│   ├── project.md
│   ├── resources.md
│   └── code/
│       ├── basic-llm/
│       │   ├── generation_params.py
│       │   ├── agent_loop.py
│       │   └── README.md
│       └── structured-output/
│           ├── classifier.py
│           └── README.md
│
├── Day-02-AI-Agents-and-Architecture/
│   ├── presentation.html
│   ├── notes.md
│   ├── hands-on.md
│   ├── project.md
│   ├── resources.md
│   └── code/
│       ├── tool-calling/
│       │   └── tool_calling.py
│       └── agent-loop/
│           └── multi_tool_agent.py
│
├── Day-03-RAG/
│   ├── presentation.html
│   ├── notes.md
│   ├── hands-on.md
│   ├── project.md
│   ├── resources.md
│   └── code/
│       ├── ingestion/
│       ├── embeddings/
│       ├── retrieval/
│       ├── rag-agent/
│       └── data/sample_policies.txt
│
├── Day-04-Agent-Frameworks-and-MCP/
│   ├── presentation.html
│   ├── notes.md
│   ├── hands-on.md
│   ├── project.md
│   ├── resources.md
│   └── code/
│       ├── langchain/
│       ├── langgraph/
│       ├── crewai/
│       └── mcp/
│
├── Day-05-Multi-Agent-Systems/
│   ├── presentation.html
│   ├── notes.md
│   ├── hands-on.md
│   ├── project.md
│   └── resources.md
│
├── Day-06-Production-AI-Agents/
│   ├── presentation.html
│   ├── notes.md
│   ├── hands-on.md
│   ├── project.md
│   ├── resources.md
│   └── code/
│       ├── fastapi/
│       ├── streaming/
│       ├── observability/
│       └── error-handling/
│
└── Day-07-End-to-End-Project/
    ├── presentation.html
    ├── requirements.md
    ├── architecture.md
    ├── tasks.md
    ├── assessment.md
    ├── resources.md
    ├── architecture/
    │   ├── specs/
    │   │   ├── agent-builder-platform.yaml
    │   │   └── it-support-multi-agent.yaml
    └── starter-code/
        ├── README.md
        ├── requirements.txt
        ├── api/app.py
        ├── agents/
        │   ├── graph.py
        │   └── load_from_spec.py
        ├── tools/tools.py
        ├── rag/
        │   ├── ingest.py
        │   └── data/*.txt
        └── tests/test_eval.py
```

## Setup

Dependencies are managed per directory with uv. From any code directory:

```bash
uv sync                  # install deps + create .venv/
cp .env.example .env     # then edit .env with your keys
uv run <script>.py       # runs inside the venv automatically
```

Required environment variables (across the week):

| Variable | Used by |
|----------|---------|
| `OPENAI_API_KEY` | Every demo (LLM calls + embeddings) |
| `LLM_MODEL` | Optional override (default: `gpt-4o-mini`) |
| `LANGFUSE_PUBLIC_KEY` | Day 6 + Day 7 (observability) |
| `LANGFUSE_SECRET_KEY` | Day 6 + Day 7 (observability) |

Each sub-directory has its own `.env.example` listing the exact variables it needs.

## License & Use

Educational use. Adapt freely for your team's training program.
