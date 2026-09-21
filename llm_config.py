"""
Single source of truth for LLM configuration.

By default this project talks to the bifrost proxy, which exposes an
OpenAI-compatible API at the ``/openai`` mount. The ``/anthropic`` mount
is only for Anthropic-format requests — sending OpenAI-format requests
there returns 405 Method Not Allowed. Auth uses a **virtual key** in
the ``x-bf-vk`` header (NOT ``Authorization: Bearer``).

To switch to direct OpenAI, set ``AI_PROVIDER=openai`` in your ``.env``.

Environment variables (see .env.example):

    AI_PROVIDER          "bifrost" (default) | "openai"
    BIFROST_BASE_URL     Proxy URL. Use ``.../openai`` — NOT ``.../anthropic``.
    BIFROST_MODEL        Model name sent to the proxy (default: minimax/minimax-m3)
    BIFROST_API_KEY      Virtual key for the proxy (sent as x-bf-vk header)
    OPENAI_API_KEY       Direct OpenAI key (only used when AI_PROVIDER=openai)
    OPENAI_MODEL         Direct OpenAI model (default: gpt-4o-mini)
    AI_FALLBACK_PROVIDER Optional. e.g. "fixture" returns canned responses offline.

Importing this module also exports the proxy URL into the standard
OpenAI env vars so downstream libraries (LangChain ``ChatOpenAI``,
LangGraph, CrewAI, …) inherit the configuration automatically.
"""
import os
import sys
import warnings

from dotenv import load_dotenv

load_dotenv()

AI_PROVIDER = os.environ.get("AI_PROVIDER", "bifrost")

# --- Bifrost proxy (default) ---
# The proxy exposes OpenAI-compatible endpoints at /openai/v1/...
# The /anthropic mount is for Anthropic-format requests (Claude).
BIFROST_BASE_URL = os.environ.get(
    "BIFROST_BASE_URL",
    "http://localhost:8000/openai",
)
BIFROST_MODEL = os.environ.get("BIFROST_MODEL", "minimax/minimax-m3")
BIFROST_API_KEY = os.environ.get("BIFROST_API_KEY", "")

# --- Direct OpenAI (fallback) ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# --- Optional fixture fallback (offline demos) ---
AI_FALLBACK_PROVIDER = os.environ.get("AI_FALLBACK_PROVIDER", "")


def _normalize_bifrost_url(url: str) -> str:
    """Drop trailing slashes and an explicit /v1 (OpenAI SDK appends /v1 itself).

    Refuses ``/anthropic`` and redirects to ``/openai`` with a loud warning,
    because the /anthropic mount only accepts Anthropic-format requests.
    Sending OpenAI-format requests to /anthropic returns 405 Method Not Allowed.
    """
    url = url.rstrip("/")
    if url.endswith("/v1"):
        url = url[:-3]
    if url.endswith("/anthropic") or "/anthropic/" in url:
        warnings.warn(
            "BIFROST_BASE_URL points at the /anthropic mount, but the OpenAI "
            "SDK sends OpenAI-format requests that the /anthropic mount "
            "rejects with 405 Method Not Allowed. Redirecting to /openai. "
            "Update your .env to set BIFROST_BASE_URL=.../openai.",
            stacklevel=2,
        )
        url = url.replace("/anthropic", "/openai")
    return url


def _export_legacy_env() -> None:
    """Mirror the chosen provider into the standard OpenAI env vars so
    downstream libraries (LangChain, LangGraph, CrewAI) inherit it
    without code edits. We FORCE the values to override any stale
    ``OPENAI_BASE_URL`` that may be set in the user's shell.
    """
    if AI_PROVIDER == "bifrost":
        base = _normalize_bifrost_url(BIFROST_BASE_URL)
        # Force-overwrite shell-set values that would otherwise bypass us.
        os.environ["OPENAI_API_BASE"] = base
        os.environ["OPENAI_BASE_URL"] = base
        os.environ["OPENAI_MODEL_NAME"] = BIFROST_MODEL
    elif AI_PROVIDER == "openai":
        os.environ["OPENAI_BASE_URL"] = "https://api.openai.com/v1"
        os.environ["OPENAI_API_BASE"] = "https://api.openai.com/v1"
        os.environ.setdefault("OPENAI_MODEL_NAME", OPENAI_MODEL)


_export_legacy_env()

from openai import OpenAI  # noqa: E402  (import after env is exported)


def _bifrost_headers() -> dict[str, str]:
    """Bifrost requires a virtual key in the x-bf-vk header."""
    if BIFROST_API_KEY:
        return {"x-bf-vk": BIFROST_API_KEY}
    return {}


def get_client() -> OpenAI:
    """Return the configured OpenAI-compatible client.

    For ``AI_PROVIDER=bifrost``, the client points at the OpenAI mount
    of the proxy and authenticates via the ``x-bf-vk`` header.

    For ``AI_PROVIDER=openai``, it talks to api.openai.com directly
    using ``Authorization: Bearer``.
    """
    if AI_PROVIDER == "bifrost":
        return OpenAI(
            api_key=BIFROST_API_KEY or "no-key",  # SDK requires this; replaced by x-bf-vk header
            base_url=_normalize_bifrost_url(BIFROST_BASE_URL),
            default_headers=_bifrost_headers(),
        )
    if AI_PROVIDER == "openai":
        return OpenAI(api_key=OPENAI_API_KEY)
    if AI_FALLBACK_PROVIDER == "fixture":
        raise RuntimeError(
            "AI_FALLBACK_PROVIDER=fixture — wire a fixture client here "
            "for offline demos."
        )
    raise ValueError(f"Unknown AI_PROVIDER: {AI_PROVIDER!r}")


def get_model() -> str:
    """Return the configured chat model name to send on every request."""
    if AI_PROVIDER == "bifrost":
        return BIFROST_MODEL
    if AI_PROVIDER == "openai":
        return OPENAI_MODEL
    raise ValueError(f"Unknown AI_PROVIDER: {AI_PROVIDER!r}")
