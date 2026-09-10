"""
BasePage: every page object inherits from this.

Why this exists: without it, each page object re-implements its own
wait/click/fill helpers, and the moment you want a default timeout, a
consistent screenshot-on-action pattern, or a logging hook, you're
editing N files instead of one. Page objects should describe WHAT is on
a page and WHAT you can do with it; BasePage owns HOW that gets done.
"""
from __future__ import annotations

import re

from playwright.sync_api import Locator, Page, expect

from framework.config.settings import settings


class BasePage:
    """Common behavior shared by every page object in the suite."""

    path: str = "/"  # overridden by subclasses, relative to ui_base_url

    def __init__(self, page: Page):
        self.page = page

    # --- navigation -----------------------------------------------------

    def goto(self) -> "BasePage":
        self.page.goto(f"{settings.ui_base_url}{self.path}")
        return self

    def title(self) -> str:
        return self.page.title()

    # --- thin, intention-revealing wrappers ------------------------------
    # These exist so tests/page objects never call raw Playwright locator
    # methods inconsistently -- every click/fill goes through one place
    # that already has the framework's default timeout applied.

    def click(self, locator: Locator) -> None:
        locator.click(timeout=settings.default_timeout_ms)

    def fill(self, locator: Locator, value: str) -> None:
        locator.fill(value, timeout=settings.default_timeout_ms)

    def text_of(self, locator: Locator) -> str:
        return locator.inner_text(timeout=settings.default_timeout_ms)

    def is_visible(self, locator: Locator) -> bool:
        return locator.is_visible()

    def expect_visible(self, locator: Locator) -> None:
        expect(locator).to_be_visible(timeout=settings.default_timeout_ms)

    def expect_text(self, locator: Locator, text: str) -> None:
        expect(locator).to_contain_text(text, timeout=settings.default_timeout_ms)

    def expect_url_contains(self, fragment: str) -> None:
        expect(self.page).to_have_url(
            re.compile(re.escape(fragment)), timeout=settings.default_timeout_ms
        )
