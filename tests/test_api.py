"""REST API E2E tests."""

from __future__ import annotations

import requests


def test_status(api):
    r = requests.get(f"{api}/v1/status")
    assert r.status_code == 200
    body = r.json()
    assert body["api"] is True
    assert body["mcp"] is True


def test_shell_execute(api):
    r = requests.post(f"{api}/v1/shell/execute", json={"cmd": "echo hello"})
    assert r.status_code == 200
    body = r.json()
    assert body["stdout"].strip() == "hello"
    assert body["exit_code"] == 0
    assert body["timed_out"] is False


def test_shell_exit_code(api):
    r = requests.post(f"{api}/v1/shell/execute", json={"cmd": "exit 42"})
    assert r.json()["exit_code"] == 42


def test_shell_timeout(api):
    r = requests.post(f"{api}/v1/shell/execute", json={"cmd": "sleep 10", "timeout": 1})
    body = r.json()
    assert body["timed_out"] is True
    assert body["exit_code"] == -1


def test_file_write_read_delete(api):
    path = "/tmp/sandbox-test-file.txt"
    content = "hello from test"

    # write
    r = requests.post(f"{api}/v1/files/write", json={"path": path, "content": content})
    assert r.status_code == 200
    assert r.json()["bytes"] == len(content.encode())

    # read
    r = requests.get(f"{api}/v1/files/read", params={"path": path})
    assert r.status_code == 200
    assert r.json()["content"] == content

    # delete
    r = requests.delete(f"{api}/v1/files/delete", params={"path": path})
    assert r.status_code == 200
    assert r.json()["deleted"] is True

    # confirm gone
    r = requests.get(f"{api}/v1/files/read", params={"path": path})
    assert r.status_code == 404


def test_file_list(api):
    r = requests.get(f"{api}/v1/files/list", params={"path": "/tmp"})
    assert r.status_code == 200
    entries = r.json()["entries"]
    assert isinstance(entries, list)


def test_healthz(nginx):
    r = requests.get(f"{nginx}/healthz")
    assert r.status_code == 200
    assert r.text.strip() == "ok"


def test_readyz(nginx):
    r = requests.get(f"{nginx}/readyz")
    assert r.status_code == 200
    body = r.json()
    assert body["api"] is True
    assert body["mcp"] is True
