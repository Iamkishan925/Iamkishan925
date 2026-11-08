"""Login lockout after repeated failures.

In-memory, so it resets on restart and assumes one backend process. That's fine
for a single-owner system; move to Redis/Postgres if the backend ever scales out.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque


class LoginLimiter:
    def __init__(self, max_failures: int, window_seconds: int):
        self.max_failures = max_failures
        self.window = window_seconds
        self._fails: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, key: str, now: float) -> deque[float]:
        q = self._fails[key]
        while q and now - q[0] > self.window:
            q.popleft()
        return q

    def blocked(self, *keys: str, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        return any(len(self._prune(k, now)) >= self.max_failures for k in keys)

    def fail(self, *keys: str, now: float | None = None) -> None:
        now = time.time() if now is None else now
        for k in keys:
            self._prune(k, now).append(now)

    def reset(self, *keys: str) -> None:
        for k in keys:
            self._fails.pop(k, None)
