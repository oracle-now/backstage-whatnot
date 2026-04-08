from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass
class SessionVerdict:
    status: str
    current_url: str
    checked_at: str
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RawOrder:
    order_id: str | None
    buyer_name: str | None
    buyer_username: str | None
    item_title: str | None
    sold_price: str | None
    quantity: str | None
    sold_at: str | None
    status: str | None
    show_id: str | None
    shipping_name: str | None
    source_page: int
    row_key: str
    raw: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Order:
    order_id: str | None
    buyer_name: str | None
    buyer_username: str | None
    buyer_key: str
    item_title: str | None
    sold_price_cents: int | None
    quantity: int
    sold_at: str | None
    status: str | None
    show_id: str | None
    shipping_name: str | None
    source_page: int
    row_key: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BundleFlag:
    buyer_key: str
    order_ids: list[str | None]
    item_titles: list[str]
    order_count: int
    same_show: bool
    bundled: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"
