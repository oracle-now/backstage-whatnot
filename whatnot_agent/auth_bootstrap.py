from __future__ import annotations

from .browser import BrowserSession, new_page
from .config import Settings
from .models import utc_now_iso
from .utils import write_json


def run(settings: Settings | None = None) -> dict:
    settings = settings or Settings()
    with BrowserSession(settings, persistent=True) as context:
        page = new_page(context)
        page.goto(settings.login_url, wait_until="domcontentloaded")
        input("Complete Whatnot login and MFA in the browser, then press Enter here to save auth state...")
        context.storage_state(path=str(settings.auth_state_path))
        result = {
            "status": "BOOTSTRAPPED",
            "auth_state_path": str(settings.auth_state_path),
            "profile_dir": str(settings.profile_dir),
            "saved_at": utc_now_iso(),
            "current_url": page.url,
        }
        write_json(settings.output_dir / "bootstrap_result.json", result)
        return result


if __name__ == "__main__":
    print(run())
