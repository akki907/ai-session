# Day 3 Project — Autonomous Research Crew

## Business Problem
A product team needs weekly competitive intelligence on AI agent platforms. Manual research takes 8 hours/week.

## Goal
Build an autonomous research pipeline that:
- Takes a topic as input.
- Decomposes it into sub-questions (Planner).
- Researches each in parallel (Researchers).
- Drafts a summary (Summarizer).
- Reviews and loops until approved (Reviewer).

## Architecture
```
User Goal
   ↓
[Planner] → sub-questions
   ↓
[Web Research]   [GitHub Research]   [Docs Research]   ← parallel
   ↓                  ↓                  ↓
[Summarizer] ← merges all
   ↓
[Reviewer] → APPROVED?  yes → final   no → loop back
```

## Framework Choice
| Need | Use |
|------|-----|
| Sequential role-based | **CrewAI** |
| Parallel fan-out + merge | **LangGraph** |
| Tool spec standardization | **MCP** |
| Simple prompt chain | **LangChain** |

## Concepts Mapped
| Concept | Implementation |
|---------|---------------|
| LangChain | Prompt templates, tool definitions |
| LangGraph | Parallel research + reviewer loop |
| CrewAI | Sequential planner/researcher/reviewer |
| MCP | Web search + GitHub search servers |
| Multi-agent | 3 researchers in parallel |
| State | LangGraph shared state object |
| HITL | Reviewer routes back to Summarizer |
