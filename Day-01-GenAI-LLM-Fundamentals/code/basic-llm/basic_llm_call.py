import sys
from pathlib import Path

# Allow `from llm_config import ...` regardless of how this file is invoked.
sys.path.insert(0, str(Path(__file__).parent))

from llm_config import get_client, get_model

client = get_client()
MODEL = get_model()

SYSTEM_PROMPT = """You are a helpful assistant that explains technical concepts
clearly to software engineers. Keep answers under 200 words."""

USER_PROMPT = "Explain the difference between temperature=0 and temperature=0.7 in one paragraph."


def call_llm(system: str, user: str) -> dict:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        max_tokens=300,
    )
    return {
        "content": response.choices[0].message.content,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
        "model": response.model,
    }


if __name__ == "__main__":
    result = call_llm(SYSTEM_PROMPT, USER_PROMPT)
    print("--- Response ---")
    print(result["content"])
    print("--- Usage ---")
    print(f"model:        {result['model']}")
    print(f"input_tokens: {result['input_tokens']}")
    print(f"output_tokens:{result['output_tokens']}")
    print(f"total_tokens: {result['total_tokens']}")
