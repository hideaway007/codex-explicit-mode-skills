#!/usr/bin/env python3
"""Append project-task-executor lifecycle events."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


EVENTS_FILE = "AGENT_EVENTS.jsonl"


def append_event(root: Path, event: str, *, task: str | None = None, **details: Any) -> None:
    root.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "ts": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "event": event,
    }
    if task is not None:
        payload["task"] = task
    if details:
        payload["details"] = details

    with (root / EVENTS_FILE).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
