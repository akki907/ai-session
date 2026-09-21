"""Per-folder shim that re-exports the shared llm_config module.

The single source of truth lives at the project root in ./llm_config.py.
Each demo folder contains this tiny shim so existing ``import llm_config``
statements keep working without modification.

Loading order for environment variables:
    1. Per-folder .env (demo-specific overrides win).
    2. Project-root .env (fallback defaults).
"""
import os
import re
import sys


_KV_LINE_RE = re.compile(
    rb"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$",
    re.MULTILINE,
)


def _load_simple_env_file(path: str) -> None:
    """Read ``path`` line by line and set ``KEY=VALUE`` entries into
    ``os.environ`` (only when not already set).
    """
    if not os.path.isfile(path):
        return
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return
    for m in _KV_LINE_RE.finditer(data):
        key = m.group(1).decode("ascii", errors="replace")
        value = m.group(2).decode("utf-8", errors="replace").strip()
        if value.startswith(('"', "'")) and value.endswith(('"', "'")):
            value = value[1:-1]
        if " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        if key not in os.environ:
            os.environ[key] = value


def _find_repo_root(start: str) -> str | None:
    """Walk UP from ``start`` until we find a directory that contains a
    canonical ``llm_config.py``.
    """
    cur = os.path.dirname(os.path.abspath(start))
    for _ in range(8):
        candidate = os.path.join(cur, "llm_config.py")
        if os.path.isfile(candidate):
            try:
                with open(candidate, "rb") as f:
                    head = f.read(16384)
            except OSError:
                head = b""
            if len(head) > 4000 and b"def _normalize_bifrost_url" in head:
                return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent
    return None


_REPO_ROOT = _find_repo_root(__file__)
if _REPO_ROOT is None:
    raise RuntimeError(
        "Could not locate the shared llm_config.py by walking up from "
        f"{os.path.dirname(os.path.abspath(__file__))!r}."
    )

# Load env files: per-folder first, then project-root fallback.
_load_simple_env_file(os.path.join(os.path.dirname(__file__), ".env"))
_load_simple_env_file(os.path.join(_REPO_ROOT, ".env"))

# Read and execute the shared file in this module's namespace. This is
# safer than ``importlib.util.spec_from_file_location`` because we don't
# trigger Python's bytecode cache machinery, which was recursing on
# certain path layouts in Python 3.12.
_shared_path = os.path.join(_REPO_ROOT, "llm_config.py")
with open(_shared_path, "r", encoding="utf-8") as f:
    _source = f.read()

# Compile with a stable filename so tracebacks remain sane.
_code = compile(_source, _shared_path, "exec")
# Use a private globals dict so we control the namespace.
_shared_globals: dict = {"__name__": "_shared_llm_config", "__file__": _shared_path}
exec(_code, _shared_globals)

# Re-export every public name from the shared module.
_globals = globals()
for _k, _v in _shared_globals.items():
    if not _k.startswith("_"):
        _globals[_k] = _v

del _globals, _k, _v, _shared_globals, _source, _code
