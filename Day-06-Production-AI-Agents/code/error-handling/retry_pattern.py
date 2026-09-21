"""
Day 6 — Retry, timeout, fallback.

Three primitives every production agent needs:
1. Retry with exponential backoff (transient failures).
2. Timeout (don't let one slow call block the whole run).
3. Fallback (return a stale cached value or a graceful "I don't know").

Setup:
    pip install tenacity httpx
Run:
    python retry_pattern.py
"""
import random
import time
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError


# --- A flaky external call ---
def flaky_external_call(should_fail: bool = False):
    if should_fail or random.random() < 0.5:
        raise ConnectionError("upstream timeout")
    return {"status": "ok"}


# --- Retry wrapper: 3 attempts, exponential backoff 1s -> 10s ---
@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
def call_with_retry(should_fail: bool = False):
    return flaky_external_call(should_fail=should_fail)


# --- Timeout wrapper using a simple deadline ---
def call_with_timeout(fn, args=(), kwargs=None, timeout_s: float = 5.0):
    kwargs = kwargs or {}
    deadline = time.time() + timeout_s
    try:
        # In real code use asyncio.wait_for; here we simulate a deadline check
        return fn(*args, **kwargs)
    except Exception as e:
        if time.time() > deadline:
            raise TimeoutError(f"exceeded {timeout_s}s")
        raise


# --- Fallback chain ---
def with_fallback(primary, fallback, *args, **kwargs):
    try:
        return primary(*args, **kwargs)
    except (RetryError, TimeoutError, ConnectionError) as e:
        print(f"  primary failed: {e} -> using fallback")
        return fallback(*args, **kwargs)


def fallback_cached(*args, **kwargs):
    return {"status": "ok_cached", "stale": True}


if __name__ == "__main__":
    print("--- retry alone ---")
    try:
        print(call_with_retry(should_fail=True))
    except RetryError:
        print("  retries exhausted")

    print("\n--- retry + fallback ---")
    print(with_fallback(call_with_retry, fallback_cached, kwargs={"should_fail": True}))

    print("\n--- transient failure recovers ---")
    print(with_fallback(call_with_retry, fallback_cached, kwargs={"should_fail": False}))
