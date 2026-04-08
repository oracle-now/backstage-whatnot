from __future__ import annotations

from .config import Settings
from .models import BundleFlag, Order, RawOrder, utc_now_iso
from .utils import parse_int, parse_price_to_cents, within_minutes, normalize_space, write_json


def _buyer_key(buyer_username: str | None, buyer_name: str | None, shipping_name: str | None) -> str:
    if buyer_username:
        return f"user:{buyer_username.strip().lower().lstrip('@')}"
    if buyer_name:
        return f"name:{normalize_space(buyer_name).lower()}"
    if shipping_name:
        return f"ship:{normalize_space(shipping_name).lower()}"
    return "unknown"


def normalize_orders(raw_orders: list[dict]) -> list[Order]:
    orders = []
    for raw in raw_orders:
        orders.append(Order(
            order_id=raw.get("order_id"),
            buyer_name=raw.get("buyer_name"),
            buyer_username=raw.get("buyer_username"),
            buyer_key=_buyer_key(raw.get("buyer_username"), raw.get("buyer_name"), raw.get("shipping_name")),
            item_title=raw.get("item_title"),
            sold_price_cents=parse_price_to_cents(raw.get("sold_price")),
            quantity=parse_int(raw.get("quantity"), 1),
            sold_at=raw.get("sold_at"),
            status=raw.get("status"),
            show_id=raw.get("show_id"),
            shipping_name=raw.get("shipping_name"),
            source_page=int(raw.get("source_page", 0)),
            row_key=raw.get("row_key") or "",
        ))
    return orders


def group_by_buyer(orders: list[Order]) -> dict[str, list[Order]]:
    groups: dict[str, list[Order]] = {}
    for order in orders:
        groups.setdefault(order.buyer_key, []).append(order)
    for buyer_key in groups:
        groups[buyer_key].sort(key=lambda order: ((order.sold_at or ""), order.order_id or ""))
    return groups


def detect_bundles(groups: dict[str, list[Order]], settings: Settings) -> list[BundleFlag]:
    flags: list[BundleFlag] = []
    for buyer_key, orders in groups.items():
        if not orders:
            continue
        cluster = [orders[0]]
        for current in orders[1:]:
            prev = cluster[-1]
            same_show = prev.show_id and current.show_id and prev.show_id == current.show_id
            close_window = within_minutes(prev.sold_at, current.sold_at, settings.bundle_window_minutes)
            if same_show or close_window:
                cluster.append(current)
            else:
                flags.append(_flag_cluster(buyer_key, cluster, settings))
                cluster = [current]
        flags.append(_flag_cluster(buyer_key, cluster, settings))
    return flags


def _flag_cluster(buyer_key: str, cluster: list[Order], settings: Settings) -> BundleFlag:
    same_show = len({order.show_id for order in cluster if order.show_id}) == 1 and any(order.show_id for order in cluster)
    bundled = len(cluster) > 1 and (same_show or within_minutes(cluster[0].sold_at, cluster[-1].sold_at, settings.bundle_window_minutes))
    return BundleFlag(
        buyer_key=buyer_key,
        order_ids=[order.order_id for order in cluster],
        item_titles=[order.item_title or "" for order in cluster],
        order_count=len(cluster),
        same_show=bool(same_show),
        bundled=bundled,
        reason="same_show_or_close_purchase_window" if bundled else "single_order_or_outside_window",
    )


def run(raw_result: dict, settings: Settings | None = None) -> dict:
    settings = settings or Settings()
    orders = normalize_orders(raw_result["orders"])
    groups = group_by_buyer(orders)
    bundles = detect_bundles(groups, settings)
    result = {
        "processed_at": utc_now_iso(),
        "normalized_order_count": len(orders),
        "buyer_group_count": len(groups),
        "bundle_count": len([b for b in bundles if b.bundled]),
        "orders": [order.to_dict() for order in orders],
        "bundles": [bundle.to_dict() for bundle in bundles],
    }
    write_json(settings.output_dir / "orders_processed.json", result)
    return result
