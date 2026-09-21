# Day 7 Project — Course Wrap-Up

## What "Done" Looks Like

By end of Day 7 each participant should be able to:

### Mental model
- Explain the difference between an LLM app and an AI agent.
- Sketch a multi-agent system on a whiteboard.
- Choose between LangChain / LangGraph / CrewAI / MCP for a given problem.

### Code
- Build a tool-calling agent from scratch (Day 1).
- Add RAG (Day 2).
- Add multi-agent routing (Day 3).
- Add streaming + retries + tracing (Day 4).
- Modify an agent spec without breaking the runtime (Day 5).
- Ship a working multi-agent system end-to-end (Day 6).

### Operations
- Read a Langfuse trace and find the slow LLM call.
- Identify the cost driver in a workflow.
- Pick the right HITL pattern for a write action.
- Set a per-user budget and explain why.

### Governance
- Spot a prompt injection in a trace.
- Decide which guardrail to add (input vs output).
- Recommend an eval cadence for production agents.

## Next 2 weeks (suggested)
1. Pick your team's first real agent use case.
2. Reuse the Day-6 starter code as a scaffold.
3. Add real MCP servers for your tools (Jira, Slack, Salesforce, etc.).
4. Ship to staging with `tests/test_eval.py` in CI.
5. Demo to your team in week 3.
