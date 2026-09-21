# Day 1 Project — LLM Fundamentals

## Business Problem
Every AI agent is built on top of an LLM. Before you can build agents, you need to understand what an LLM actually is, what it can and can't do, and how to talk to it well.

## Goal
Build the **mental model** you need to design, debug, and evaluate AI agents. By the end of Day 1 you should be able to:
- Explain how a transformer processes text.
- Predict when an LLM will hallucinate and how to mitigate it.
- Tune generation parameters (temperature, top-p, max_tokens) for a task.
- Write good prompts and spot prompt injection.
- Read an "AI Agent" definition and know whether it's real marketing or substance.

## Architecture
This day is **concept-first, code-second**:
```
How LLMs work
   ↓
What they're good / bad at
   ↓
How to control them (prompts + params)
   ↓
What they're vulnerable to (injection, hallucination)
   ↓
→ ready to design AI agents (Day 2)
```

## Concepts Covered
| Concept | Where in Day 1 |
|---------|---------------|
| AI hierarchy (AI → ML → DL → GenAI → LLM) | Slide 4 |
| Transformer architecture (attention, FF, layers) | Slides 5–6 |
| Pre-training vs Fine-tuning | Slide 7 |
| LLM limitations | Slide 8 |
| Hallucination — root causes + mitigations | Slide 9 |
| Generation parameters (temp, top-p, max_tokens, stop, …) | Slides 10–11 |
| Good vs Bad prompts | Slide 12 |
| Prompt engineering patterns (zero-shot, few-shot, role, CoT, structured output, JSON schema) | Slides 13–14 |
| Prompt injection — direct, indirect, tool-output | Slide 15 |

## What Day 1 Does NOT Do
- ✗ No agent loop (Day 2)
- ✗ No tools, memory, planning, reasoning (Day 2)
- ✗ No RAG / vector DB (Day 3)
- ✗ No multi-agent (Day 5–6)
- ✗ No production API (Day 4)

## Hands-on outcome
You'll write small Python scripts that classify text, generate with varying temperature, and try a prompt injection attack — all to build intuition, not to ship anything.
