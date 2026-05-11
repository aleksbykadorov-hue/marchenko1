# -*- coding: utf-8 -*-
"""
Интеграционный сценарий: 2 пользователя → чат → сообщения от обоих.
Требуется запущенный стек: docker compose up -d

Запуск (из корня репозитория или откуда угодно):
  python scripts/run_integration_scenario.py

Сделай скриншот терминала с выводом (блоки OK и итог INTEGRATION SCENARIO PASSED).
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any

USER_API = "http://127.0.0.1:8001"
CHAT_API = "http://127.0.0.1:8002"


def _req(
    method: str,
    url: str,
    *,
    json_body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, Any]:
    h = {"Content-Type": "application/json", **(headers or {})}
    data = json.dumps(json_body).encode("utf-8") if json_body is not None else None
    r = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            code = resp.status
            if not raw:
                return code, None
            return code, json.loads(raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            body = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            body = raw
        return e.code, body


def main() -> int:
    ts = int(time.time())
    email1 = f"demo1.{ts}@example.com"
    email2 = f"demo2.{ts}@example.com"
    password = "secret12"

    print("=" * 60)
    print("  INTEGRATION SCENARIO (user-service + chat-service)")
    print("=" * 60)
    print(f"  user API: {USER_API}")
    print(f"  chat API: {CHAT_API}")
    print()

    # --- User 1 ---
    code, u1 = _req("POST", f"{USER_API}/auth/register", json_body={"email": email1, "password": password})
    if code != 201:
        print(f"[FAIL] register user1: HTTP {code} {u1}")
        return 1
    id1 = u1["id"]
    print(f"[OK]   registered user1: id={id1} email={email1}")

    code, u2 = _req("POST", f"{USER_API}/auth/register", json_body={"email": email2, "password": password})
    if code != 201:
        print(f"[FAIL] register user2: HTTP {code} {u2}")
        return 1
    id2 = u2["id"]
    print(f"[OK]   registered user2: id={id2} email={email2}")

    code, t1 = _req("POST", f"{USER_API}/auth/login", json_body={"email": email1, "password": password})
    if code != 200:
        print(f"[FAIL] login user1: HTTP {code} {t1}")
        return 1
    token1 = t1["access_token"]
    print("[OK]   login user1 -> JWT ok")

    code, t2 = _req("POST", f"{USER_API}/auth/login", json_body={"email": email2, "password": password})
    if code != 200:
        print(f"[FAIL] login user2: HTTP {code} {t2}")
        return 1
    token2 = t2["access_token"]
    print("[OK]   login user2 -> JWT ok")

    auth1 = {"Authorization": f"Bearer {token1}"}
    auth2 = {"Authorization": f"Bearer {token2}"}

    # --- Chat ---
    code, chat = _req(
        "POST",
        f"{CHAT_API}/chats",
        json_body={"title": f"Integration group {ts}"},
        headers=auth1,
    )
    if code != 201:
        print(f"[FAIL] create chat: HTTP {code} {chat}")
        return 1
    chat_id = chat["id"]
    print(f"[OK]   chat created id={chat_id} (owner user1)")

    code, _ = _req(
        "POST",
        f"{CHAT_API}/chats/{chat_id}/members",
        json_body={"user_id": id2, "role": "member"},
        headers=auth1,
    )
    if code != 204:
        print(f"[FAIL] add user2 to chat: HTTP {code}")
        return 1
    print(f"[OK]   user2 id={id2} added to chat")

    code, m1 = _req(
        "POST",
        f"{CHAT_API}/chats/{chat_id}/messages",
        json_body={"text": "Message from user one"},
        headers=auth1,
    )
    if code != 201:
        print(f"[FAIL] message from user1: HTTP {code} {m1}")
        return 1
    print(f"[OK]   message #1 from user1: id={m1['id']}")

    code, m2 = _req(
        "POST",
        f"{CHAT_API}/chats/{chat_id}/messages",
        json_body={"text": "Reply from user two"},
        headers=auth2,
    )
    if code != 201:
        print(f"[FAIL] message from user2: HTTP {code} {m2}")
        return 1
    print(f"[OK]   message #2 from user2: id={m2['id']}")

    code, msgs = _req("GET", f"{CHAT_API}/chats/{chat_id}/messages?limit=20&offset=0", headers=auth1)
    if code != 200:
        print(f"[FAIL] list messages: HTTP {code} {msgs}")
        return 1
    print(f"[OK]   messages in thread: {len(msgs)}")
    for i, row in enumerate(msgs, 1):
        aid = row.get("author_user_id")
        print(f"       {i}. author_user_id={aid} text={row.get('text')!r}")

    print()
    print("=" * 60)
    print("  INTEGRATION SCENARIO PASSED (screenshot this terminal output)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except urllib.error.URLError as e:
        print(f"[FAIL] cannot reach API: {e}")
        print("       Start stack: docker compose up -d (project root)")
        sys.exit(1)
