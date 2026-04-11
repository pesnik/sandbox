"""
E2E test fixtures.

Expects the sandbox container to already be running (make up).
Uses SANDBOX_BASE_URL env var (default: http://localhost:8091).
"""

from __future__ import annotations

import os
import time

import pytest
import requests

BASE_URL  = os.getenv("SANDBOX_BASE_URL",  "http://localhost:8091")
MCP_URL   = os.getenv("SANDBOX_MCP_URL",   "http://localhost:8079")
NGINX_URL = os.getenv("SANDBOX_NGINX_URL", "http://localhost:8080")


def wait_for_ready(url: str, timeout: int = 30) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{url}/v1/status", timeout=2)
            if r.status_code == 200:
                return
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    raise RuntimeError(f"sandbox not ready at {url} after {timeout}s")


@pytest.fixture(scope="session", autouse=True)
def sandbox_ready():
    wait_for_ready(BASE_URL)


@pytest.fixture(scope="session")
def api():
    return BASE_URL


@pytest.fixture(scope="session")
def mcp():
    return MCP_URL


@pytest.fixture(scope="session")
def nginx():
    return NGINX_URL
