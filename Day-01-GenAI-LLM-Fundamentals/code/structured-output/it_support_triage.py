import json
import sys
from enum import Enum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field, ValidationError

# Allow `from llm_config import ...` regardless of how this file is invoked.
sys.path.insert(0, str(Path(__file__).parent))
from llm_config import get_client, get_model

client = get_client()
MODEL = get_model()


class Category(str, Enum):
    VPN = "VPN"
    LAPTOP = "Laptop"
    PASSWORD = "Password"
    SOFTWARE = "Software"
    ACCESS = "Access"
    TICKET_STATUS = "Ticket Status"
    POLICY = "Policy"
    OTHER = "Other"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ─────────────────────────────────────────────────────────────────────────
# Category alias map
# ─────────────────────────────────────────────────────────────────────────
# Different models pick different category names for the same concept
# (e.g. minimax/minimax-m3 returns "network" for a VPN issue, "auth"
# for a password issue). We normalize before enum validation so the demo
# is robust across providers without losing the strictness of the enum.
#
# Canonical names MUST match Category members exactly.
# Keys are matched case-insensitively after whitespace trimming.
CATEGORY_ALIASES: dict[str, str] = {
    # VPN / network / connectivity
    "vpn": "VPN",
    "network": "VPN",
    "networking": "VPN",
    "connectivity": "VPN",
    "wifi": "VPN",
    "internet": "VPN",
    "lan": "VPN",
    # Laptop / hardware / device
    "laptop": "Laptop",
    "hardware": "Laptop",
    "device": "Laptop",
    "machine": "Laptop",
    "computer": "Laptop",
    "pc": "Laptop",
    # Password / credentials / login
    "password": "Password",
    "credentials": "Password",
    "credential": "Password",
    "login": "Password",
    "log-in": "Password",
    "log in": "Password",
    "auth": "Password",
    "authentication": "Password",
    "mfa": "Password",
    "2fa": "Password",
    # Software / app / install
    "software": "Software",
    "app": "Software",
    "application": "Software",
    "tool": "Software",
    "install": "Software",
    "installation": "Software",
    "update": "Software",
    # Access / permissions / RBAC
    "access": "Access",
    "permission": "Access",
    "permissions": "Access",
    "rbac": "Access",
    "grant": "Access",
    "role": "Access",
    # Ticket status / incident lookup
    "ticket": "Ticket Status",
    "tickets": "Ticket Status",
    "status": "Ticket Status",
    "incident": "Ticket Status",
    "inc": "Ticket Status",
    # Policy / docs / guideline
    "policy": "Policy",
    "policies": "Policy",
    "rule": "Policy",
    "guideline": "Policy",
    "documentation": "Policy",
    "doc": "Policy",
    "docs": "Policy",
    # Other catch-all
    "other": "Other",
}


def _normalize_category(value):
    """Map a model-returned category string onto the canonical enum value.

    - Strips whitespace and lowercases.
    - Looks the result up in CATEGORY_ALIASES.
    - Returns the canonical string if a match is found, else returns the
      original value (which will then fail enum validation loudly — good
      for debugging).
    """
    if isinstance(value, str):
        key = value.strip().lower()
        return CATEGORY_ALIASES.get(key, value)
    return value


class TriageDecision(BaseModel):
    category: Annotated[Category, BeforeValidator(_normalize_category)]
    priority: Priority
    suggested_action: str = Field(min_length=1)
    requires_ticket: bool
    reasoning: str = Field(min_length=1)


SYSTEM_PROMPT = (
    "You are an enterprise IT support triage assistant.\n\n"
    "Your job is to read a user's IT support message and produce a triage decision.\n\n"
    "Rules:\n"
    "- Do not invent information about the user's environment.\n"
    "- Choose exactly one category from this canonical list (use these exact "
    "strings; synonyms like 'network', 'auth', 'app' will be normalized "
    "automatically):\n"
    "  * VPN            — VPN, network, connectivity, Wi-Fi, internet issues\n"
    "  * Laptop         — laptop, hardware, device, computer problems\n"
    "  * Password       — password, credentials, login, MFA, 2FA issues\n"
    "  * Software       — app, application, tool, install, update issues\n"
    "  * Access         — access, permission, RBAC, role, grant requests\n"
    "  * Ticket Status  — checking the status of an existing ticket/incident\n"
    "  * Policy         — policy, rule, guideline, documentation questions\n"
    "  * Other          — anything that does not fit the categories above\n"
    "- Choose priority based on user impact:\n"
    "  * high: blocks work, security incident, production down\n"
    "  * medium: degraded work, common request\n"
    "  * low: informational, request for documentation\n"
    "- suggested_action must be a short imperative verb phrase "
    "(e.g. restart_vpn_client).\n"
    "- requires_ticket is true when the issue cannot be resolved by self-service.\n"
    "- reasoning must be one short sentence.\n\n"
    "Output format (strict):\n"
    "Return a single JSON object with these fields:\n"
    "- category\n"
    "- priority\n"
    "- suggested_action\n"
    "- requires_ticket\n"
    "- reasoning"
)


def build_user_prompt(message: str) -> str:
    return (
        f"User IT support message:\n\n{message}\n\n"
        "Produce the triage JSON."
    )


def call_triage(message: str) -> TriageDecision:
    """Call the LLM and validate the triage decision.

    Retries once with a stricter prompt if the model returns invalid JSON.
    Category synonyms are normalized via CATEGORY_ALIASES before enum
    validation, so 'network' -> VPN, 'auth' -> Password, etc.
    """
    last_error: Exception | None = None

    for attempt in (1, 2):
        system = SYSTEM_PROMPT
        if attempt == 2:
            system = (
                SYSTEM_PROMPT
                + "\n\nIMPORTANT: Your previous output was invalid. "
                + "Respond with ONLY the JSON object, no prose, no markdown."
            )

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": build_user_prompt(message)},
            ],
            temperature=0.0,
            max_tokens=400,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content

        try:
            data = json.loads(raw)
            decision = TriageDecision.model_validate(data)
            return decision
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = e
            continue

    raise RuntimeError(f"Triage failed after retry: {last_error}")


if __name__ == "__main__":
    samples = [
        "My VPN is not working. I cannot connect from home.",
        "I forgot my laptop password.",
        "Where can I find the company's remote work policy?",
        "I need access to the production AWS account.",
        "Check the status of INC-12345.",
    ]
    for m in samples:
        decision = call_triage(m)
        print(f"> {m}")
        print(decision.model_dump_json(indent=2))
        print()
