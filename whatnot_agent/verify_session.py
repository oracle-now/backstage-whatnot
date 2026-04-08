from __future__ import annotations

from .browser import BrowserSession, new_page
from .config import Settings
from .locators import LOGIN_MARKERS
from .models import SessionVerdict, utc_now_iso
from .utils import write_json


def _on_login_route(url: str) -> bool:
    url = (url or "").lower()
    return any(part in url for part in ["/login", "/signin", "/auth"])


def _looks_logged_in(page) -> bool:
    if _on_login_route(page.url):
        return False
    for selector in LOGIN_MARKERS:
        try:
            if page.locator(selector).first.is_visible(timeout=800):
                return True
        except Exception:
            continue
    return any(part in page.url.lower() for part in ["/seller", "/dashboard", "/orders", "/inventory", "/payouts"])


def _looks_checkpointed(page) -> bool:
    try:
        text = page.locator("body").inner_text(timeout=1200).lower()
    except Exception:
        text = ""
    patterns = [
        "captcha", "verify you are human", "security check", "verification code",
        "two-factor", "2fa", "one-time code", "check your email", "check your phone",
    ]
    return any(p in text for p in patterns) or "challenge" in page.url.lower()


def run(settings: Settings | None = None) -> dict:
    settings = settings or Settings()
    with BrowserSession(settings, persistent=False) as context:
        page = new_page(context)
        page.goto(settings.base_url, wait_until="domcontentloaded")
        if _looks_checkpointed(page):
            verdict = SessionVerdict(status="CHECKPOINT", current_url=page.url, checked_at=utc_now_iso(), reason="checkpoint_detected")
        elif _looks_logged_in(page):
            verdict = SessionVerdict(status="VALID", current_url=page.url, checked_at=utc_now_iso())
        else:
            verdict = SessionVerdict(status="EXPIRED", current_url=page.url, checked_at=utc_now_iso(), reason="not_authenticated")
        write_json(settings.output_dir / "session_verdict.json", verdict.to_dict())
        return verdict.to_dict()


if __name__ == "__main__":
    print(run())
