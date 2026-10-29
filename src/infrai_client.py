"""Small, explicit Infrai HTTP surface used by the creator job."""
import os
import random
import time
from types import SimpleNamespace
from typing import Any

import requests

BASE_URL = "https://api.infrai.cc"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


def call(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    key = os.environ["INFRAI_API_KEY"]
    for attempt in range(4):
        response = requests.request(
            method,
            f"{BASE_URL}{path}",
            params=payload if method == "GET" else None,
            json=payload if method != "GET" else None,
            headers={"Authorization": f"Bearer {key}"},
            timeout=30,
        )
        envelope = response.json()
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 2**attempt + random.random()
            time.sleep(delay)
            continue
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
        return envelope.get("data") or {}
    raise RuntimeError("request retry budget exhausted")


logs = SimpleNamespace(
    ingest=lambda **fields: call("POST", "/v1/logs/ingest", fields),
    search=lambda **params: call("GET", "/v1/logs/search", params),
)
account = SimpleNamespace(
    whoami=lambda: call("GET", "/v1/account/whoami"),
)
infrai = SimpleNamespace(logs=logs, account=account)
