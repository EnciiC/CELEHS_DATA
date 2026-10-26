"""Public hosting settings and small process-local abuse controls."""
from __future__ import annotations

import os
import re
import time
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass
from urllib.parse import urlparse

from fastapi import HTTPException


def provider():
    value = os.environ.get("CATALOG_PROVIDER", "ollama").strip().lower()
    if value not in {"ollama", "cloudflare"}:
        raise ValueError("Unknown model provider")
    return value


@dataclass(frozen=True)
class Hosting:
    public: bool
    hosts: tuple[str, ...]
    origins: frozenset[str]

    @classmethod
    def from_env(cls):
        public = provider() == "cloudflare"
        hosts = ["localhost", "127.0.0.1", "testserver"]
        origins = {"http://127.0.0.1:8000", "http://localhost:8000", "http://testserver"}
        if public:
            hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
            if hostname:
                if not re.fullmatch(r"[a-z0-9-]+\.onrender\.com", hostname):
                    raise ValueError("Invalid Render hostname")
                hosts.append(hostname)
                origins.add("https://" + hostname)
            custom = os.environ.get("CATALOG_PUBLIC_ORIGIN", "").strip()
            if custom:
                parsed = urlparse(custom)
                if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
                        or parsed.path or parsed.query or parsed.fragment or parsed.port):
                    raise ValueError("Public origin must be an HTTPS origin without a path")
                hosts.append(parsed.hostname)
                origins.add(custom)
        return cls(public, tuple(hosts), frozenset(origins))


class ChatLimits:
    """Single-worker limits, reset on restart. Gateway budgets remain necessary."""
    def __init__(self, per_minute=8, per_day=200, concurrent=2):
        self.minute = deque()
        self.day = deque()
        self.active = 0
        self.per_minute, self.per_day, self.concurrent = per_minute, per_day, concurrent

    @asynccontextmanager
    async def slot(self):
        now = time.monotonic()
        for queue, window in [(self.minute, 60), (self.day, 86400)]:
            while queue and queue[0] <= now - window:
                queue.popleft()
        if self.active >= self.concurrent or len(self.minute) >= self.per_minute or len(self.day) >= self.per_day:
            raise HTTPException(429, "Chat is busy or its request limit was reached. Please try later. You can still browse datasets.",
                                headers={"Retry-After": "60"})
        self.minute.append(now)
        self.day.append(now)
        self.active += 1
        try:
            yield
        finally:
            self.active -= 1
