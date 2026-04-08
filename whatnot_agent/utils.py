from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path


def write_json(path: Path, payload: dict | list) -> None:
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def parse_price_to_cents(value: str | None) -> int | None:
    if not value:
        return None
    cleaned = re.sub(r"[^\d.]", "", value)
    if not cleaned:
        return None
    return int(round(float(cleaned) * 100))


def parse_int(value: str | None, default: int = 1) -> int:
    if not value:
        return default
    match = re.search(r"\d+", value)
    return int(match.group(0)) if match else default


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    formats = [
        "%b %d, %Y, %I:%M %p",
        "%B %d, %Y, %I:%M %p",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def within_minutes(a: str | None, b: str | None, minutes: int) -> bool:
    dt_a = parse_datetime(a)
    dt_b = parse_datetime(b)
    if dt_a is None or dt_b is None:
        return False
    return abs(dt_b - dt_a) <= timedelta(minutes=minutes)


def normalize_space(value: str | None) -> str | None:
    if value is None:
        return None
    return re.sub(r"\s+", " ", value).strip() or None
