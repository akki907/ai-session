"""
Day 4 — CrewAI research crew: Planner → Researcher → Reviewer.

CrewAI's ``Agent`` uses OpenAI under the hood. Importing ``llm_config``
exports ``OPENAI_API_BASE`` so all LLM calls automatically go through
the configured proxy (bifrost by default).

Setup:
    uv sync
    cp .env.example .env
Run:
    uv run research_crew.py
"""
import json
import os
import sys
from pathlib import Path

from crewai import Agent, Task, Crew, Process
from crewai_tools import tool

# Importing llm_config exports proxy env vars so CrewAI inherits the
# bifrost / OpenAI configuration without code edits.
sys.path.insert(0, str(Path(__file__).parent))
import llm_config  # noqa: F401  (side-effect: sets OPENAI_API_BASE)


@tool("fake_search")
def fake_search(q: str) -> str:
    """Mock web search returning canned findings."""
    return json.dumps({
        "q": q,
        "results": [
            f"Mock finding 1 for {q}",
            f"Mock finding 2 for {q}",
        ]
    })


def build_crew(topic: str) -> Crew:
    planner = Agent(
        role="Planner",
        goal="Decompose the topic into 3 focused sub-questions.",
        backstory="Expert research strategist.",
    )
    researcher = Agent(
        role="Researcher",
        goal="Find authoritative answers to the sub-questions.",
        backstory="Senior analyst with web search skills.",
        tools=[fake_search],
    )
    reviewer = Agent(
        role="Reviewer",
        goal="Verify findings, flag weak or unsupported claims.",
        backstory="Fact-checker.",
    )

    plan_task = Task(
        description=f"Create 3 sub-questions to research about: {topic}.",
        expected_output="A JSON list of 3 questions.",
        agent=planner,
    )
    research_task = Task(
        description="For each sub-question, use fake_search to gather findings.",
        expected_output="A JSON object mapping each question to its findings.",
        agent=researcher,
    )
    review_task = Task(
        description="Review the findings. Output APPROVED or NEEDS_WORK with reasons.",
        expected_output="Status string plus brief rationale.",
        agent=reviewer,
    )

    return Crew(
        agents=[planner, researcher, reviewer],
        tasks=[plan_task, research_task, review_task],
        process=Process.sequential,
    )


if __name__ == "__main__":
    crew = build_crew("agent observability")
    print(crew.kickoff(inputs={"topic": "agent observability"}))
