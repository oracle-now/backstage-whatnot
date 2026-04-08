from __future__ import annotations

from pathlib import Path
from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

from .config import Settings, ensure_dirs


class BrowserSession:
    def __init__(self, settings: Settings, persistent: bool = False):
        self.settings = settings
        self.persistent = persistent
        self._pw: Playwright | None = None
        self.context: BrowserContext | None = None

    def __enter__(self) -> BrowserContext:
        ensure_dirs(self.settings)
        self._pw = sync_playwright().start()
        if self.persistent:
            self.context = self._pw.chromium.launch_persistent_context(
                user_data_dir=str(self.settings.profile_dir.resolve()),
                headless=False,
            )
        else:
            storage_state = str(self.settings.auth_state_path) if self.settings.auth_state_path.exists() else None
            browser = self._pw.chromium.launch(headless=self.settings.headless)
            self.context = browser.new_context(storage_state=storage_state)
        self.context.set_default_timeout(15000)
        self.context.set_default_navigation_timeout(20000)
        return self.context

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.context:
            self.context.close()
        if self._pw:
            self._pw.stop()


def new_page(context: BrowserContext) -> Page:
    page = context.new_page()
    return page
