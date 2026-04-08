from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("WHATNOT_BASE_URL", "https://www.whatnot.com")
    login_url: str = os.getenv("WHATNOT_LOGIN_URL", "https://www.whatnot.com/login")
    auth_state_path: Path = Path(os.getenv("WHATNOT_AUTH_STATE_PATH", "artifacts/auth_state.json"))
    profile_dir: Path = Path(os.getenv("WHATNOT_PROFILE_DIR", "artifacts/profile"))
    output_dir: Path = Path(os.getenv("WHATNOT_OUTPUT_DIR", "artifacts"))
    headless: bool = os.getenv("WHATNOT_HEADLESS", "true").lower() == "true"
    manual_login_timeout_seconds: int = int(os.getenv("WHATNOT_MANUAL_LOGIN_TIMEOUT_SECONDS", "600"))
    max_pages: int = int(os.getenv("WHATNOT_MAX_PAGES", "50"))
    bundle_window_minutes: int = int(os.getenv("WHATNOT_BUNDLE_WINDOW_MINUTES", "15"))
    sold_orders_candidates: tuple[str, ...] = field(default_factory=lambda: tuple(
        u for u in [
            os.getenv("WHATNOT_SOLD_ORDERS_URL", "").strip(),
            "https://www.whatnot.com/seller/orders",
            "https://www.whatnot.com/seller/sold-orders",
            "https://www.whatnot.com/seller",
            "https://www.whatnot.com/dashboard/orders",
            "https://www.whatnot.com/orders",
        ] if u
    ))


def ensure_dirs(settings: Settings) -> None:
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.profile_dir.mkdir(parents=True, exist_ok=True)
    settings.auth_state_path.parent.mkdir(parents=True, exist_ok=True)
