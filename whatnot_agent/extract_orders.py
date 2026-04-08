from __future__ import annotations

import re
from typing import Iterable

from .browser import BrowserSession, new_page
from .config import Settings
from .locators import NEXT_PAGE, ORDERS_ROOTS, ORDER_ROWS
from .models import RawOrder, utc_now_iso
from .utils import write_json
from .verify_session import run as verify_session


def _extract_by_patterns(text: str, patterns: list[str], prefix: str = "") -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text or "", flags=re.IGNORECASE)
        if match:
            return f"{prefix}{match.group(1).strip()}"
    return None


def _extract_cells(row) -> list[str]:
    for tag in ["td", "[role='cell']", "div"]:
        try:
            cells = row.locator(tag)
            count = cells.count()
            values = []
            for i in range(min(count, 8)):
                text = cells.nth(i).inner_text().strip()
                if text:
                    values.append(text)
            if values:
                return values
        except Exception:
            continue
    return []


def _row_locator(page):
    for selector in ORDER_ROWS:
        loc = page.locator(selector)
        try:
            if loc.count() > 0:
                return loc
        except Exception:
            continue
    return page.locator("tr")


def _looks_like_orders_page(page) -> bool:
    score = 0
    try:
        text = page.locator("body").inner_text(timeout=1500).lower()
    except Exception:
        text = ""
    if "order" in page.url.lower():
        score += 2
    if any(term in text for term in ["sold orders", "buyer", "order #", "status", "quantity"]):
        score += 2
    for selector in ORDERS_ROOTS:
        try:
            if page.locator(selector).first.is_visible(timeout=800):
                score += 1
                break
        except Exception:
            continue
    try:
        if _row_locator(page).count() > 0:
            score += 1
    except Exception:
        pass
    return score >= 3


def _goto_orders(page, settings: Settings) -> None:
    for url in settings.sold_orders_candidates:
        page.goto(url, wait_until="domcontentloaded")
        if _looks_like_orders_page(page):
            return
        for candidate in [
            page.get_by_role("link", name=re.compile(r"sold orders|orders", re.I)).first,
            page.get_by_role("button", name=re.compile(r"sold orders|orders", re.I)).first,
            page.locator("a[href*='order' i]").first,
            page.locator("button:has-text('Orders')").first,
        ]:
            try:
                if candidate.is_visible(timeout=800):
                    candidate.click()
                    page.wait_for_timeout(1000)
                    if _looks_like_orders_page(page):
                        return
            except Exception:
                continue
    raise RuntimeError("ROUTE_DRIFT: Could not locate the Whatnot orders page")


def _page_marker(page) -> str:
    try:
        rows = _row_locator(page)
        if rows.count() == 0:
            return page.url
        return page.url + "|" + rows.nth(0).inner_text()[:200]
    except Exception:
        return page.url


def _next_page(page) -> bool:
    before = _page_marker(page)
    for selector in NEXT_PAGE:
        try:
            candidate = page.locator(selector).first
            if not candidate.is_visible(timeout=800):
                continue
            if candidate.get_attribute("disabled") is not None:
                return False
            if candidate.get_attribute("aria-disabled") == "true":
                return False
            candidate.click()
            page.wait_for_timeout(1200)
            return _page_marker(page) != before
        except Exception:
            continue
    return False


def _extract_row_data(row) -> dict:
    try:
        text = row.inner_text().strip()
    except Exception:
        text = ""
    cells = _extract_cells(row)
    data = {
        "order_id": _extract_by_patterns(text, [r"Order\s*#?\s*([A-Z0-9-]+)", r"#([A-Z0-9-]{6,})"]),
        "buyer_name": cells[0].strip() if len(cells) > 0 else None,
        "buyer_username": _extract_by_patterns(text, [r"@([A-Za-z0-9._-]+)"], "@"),
        "item_title": cells[1].strip() if len(cells) > 1 else None,
        "sold_price": _extract_by_patterns(text, [r"(\$\s?\d[\d,]*(?:\.\d{2})?)"])  ,
        "quantity": _extract_by_patterns(text, [r"\bQty[:\s]+(\d+)\b", r"\bQuantity[:\s]+(\d+)\b"]),
        "sold_at": _extract_by_patterns(text, [r"([A-Z][a-z]{2,8}\s+\d{1,2},\s+\d{4},?\s+\d{1,2}:\d{2}\s*(?:AM|PM)?)", r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?)"])  ,
        "status": next((s for s in ["Paid", "Pending", "Shipped", "Delivered", "Canceled", "Cancelled", "Refunded"] if s.lower() in text.lower()), None),
        "show_id": _extract_by_patterns(text, [r"Show\s*#?\s*([A-Z0-9-]+)"]),
        "shipping_name": None,
        "text": text,
        "cells": cells,
    }
    return data if any([data["order_id"], data["buyer_name"], data["item_title"], data["sold_price"]]) else {}


def run(settings: Settings | None = None) -> dict:
    settings = settings or Settings()
    verdict = verify_session(settings)
    if verdict["status"] != "VALID":
        raise RuntimeError(f"AUTH_{verdict['status']}: session verification failed")
    with BrowserSession(settings, persistent=False) as context:
        page = new_page(context)
        _goto_orders(page, settings)
        rows: list[RawOrder] = []
        seen = set()
        page_number = 1
        while page_number <= settings.max_pages:
            locator = _row_locator(page)
            count = locator.count()
            for idx in range(count):
                raw = _extract_row_data(locator.nth(idx))
                if not raw:
                    continue
                order_id = raw.get("order_id") or f"page{page_number}-row{idx}"
                row_key = "|".join(x.strip().lower() for x in [raw.get("order_id") or "", raw.get("buyer_username") or "", raw.get("item_title") or "", raw.get("sold_price") or "", raw.get("sold_at") or ""] if x) or f"{order_id}:{page_number}:{idx}"
                if row_key in seen:
                    continue
                seen.add(row_key)
                rows.append(RawOrder(order_id=order_id, buyer_name=raw.get("buyer_name"), buyer_username=raw.get("buyer_username"), item_title=raw.get("item_title"), sold_price=raw.get("sold_price"), quantity=raw.get("quantity"), sold_at=raw.get("sold_at"), status=raw.get("status"), show_id=raw.get("show_id"), shipping_name=raw.get("shipping_name"), source_page=page_number, row_key=row_key, raw=raw))
            if not _next_page(page):
                break
            page_number += 1
        result = {
            "scraped_at": utc_now_iso(),
            "final_url": page.url,
            "raw_order_count": len(rows),
            "orders": [row.to_dict() for row in rows],
        }
        write_json(settings.output_dir / "orders_raw.json", result)
        return result


if __name__ == "__main__":
    print(run())
