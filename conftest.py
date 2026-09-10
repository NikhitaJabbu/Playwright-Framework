"""
Root pytest config: markers, storageState-based auth reuse, and
trace/screenshot/video capture on failure.

This file is what turns "a folder of Playwright scripts" into a
framework. Specifically:

1. `authenticated_page` fixture logs in ONCE per test session and saves
   Playwright's storageState to disk; every test that needs a logged-in
   session reuses that state instead of re-running the login flow. This
   is the single highest-leverage perf/flake fix in UI automation.
2. `pytest_runtest_makereport` hook + the `context`/`page` fixtures below
   wire up tracing so that ONLY failing tests keep their trace/video/
   screenshot artifacts -- passing tests don't bloat CI storage.
3. Custom markers (`smoke`, `regression`, `api`, `visual`) let CI or a
   dev run subsets: `pytest -m smoke`.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext, Page

from framework.config.settings import settings
from framework.pages.login_page import LoginPage

ARTIFACTS_DIR = Path(__file__).resolve().parent / "test-results" / "artifacts"


def pytest_configure(config: pytest.Config) -> None:
    for marker, desc in [
        ("smoke", "fast, critical-path checks -- runs on every push"),
        ("regression", "full coverage -- runs on schedule / pre-release"),
        ("api", "tests that hit the API target only, no browser needed"),
        ("visual", "screenshot-comparison visual regression tests"),
    ]:
        config.addinivalue_line("markers", f"{marker}: {desc}")

    settings.auth_storage_dir.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Browser context per test, with tracing always started so we can choose
# after the test whether to keep the trace (only on failure).
# ---------------------------------------------------------------------------


@pytest.fixture
def context(browser: Browser, request: pytest.FixtureRequest) -> BrowserContext:
    context = browser.new_context()
    context.set_default_timeout(settings.default_timeout_ms)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield context

    test_name = request.node.name.replace("/", "_")
    failed = request.node.rep_call.failed if hasattr(request.node, "rep_call") else False

    if failed:
        trace_path = ARTIFACTS_DIR / f"{test_name}-trace.zip"
        context.tracing.stop(path=str(trace_path))
    else:
        context.tracing.stop()

    context.close()


@pytest.fixture
def page(context: BrowserContext, request: pytest.FixtureRequest) -> Page:
    page = context.new_page()
    yield page

    failed = request.node.rep_call.failed if hasattr(request.node, "rep_call") else False
    if failed:
        test_name = request.node.name.replace("/", "_")
        screenshot_path = ARTIFACTS_DIR / f"{test_name}-failure.png"
        try:
            page.screenshot(path=str(screenshot_path), full_page=True)
        except Exception:
            pass  # page may already be closed/crashed -- don't mask the real failure


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Stash the outcome of each phase on the test item so fixtures above
    can check `rep_call.failed` during their own teardown."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# ---------------------------------------------------------------------------
# Authenticated session reuse (storageState) -- the auth-reuse pattern
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def auth_storage_state_path(browser: Browser) -> str:
    """Logs in once for the whole test session and persists storageState
    to disk. Individual tests ask for `authenticated_page` below rather
    than using this fixture directly."""
    storage_file = settings.auth_storage_dir / f"{settings.env}-standard-user.json"

    context = browser.new_context()
    page = context.new_page()
    LoginPage(page).goto().login(settings.ui_username, settings.ui_password)
    page.wait_for_url("**/inventory.html")
    context.storage_state(path=str(storage_file))
    context.close()

    yield str(storage_file)

    # cleanup at end of session so stale auth never leaks into another run
    if storage_file.exists():
        storage_file.unlink()


@pytest.fixture
def authenticated_page(browser: Browser, auth_storage_state_path: str) -> Page:
    """A Page that's already logged in, via a reused storageState -- no
    login flow re-run per test. This is the fixture most UI tests want."""
    context = browser.new_context(storage_state=auth_storage_state_path)
    context.set_default_timeout(settings.default_timeout_ms)
    page = context.new_page()
    yield page
    context.close()


# ---------------------------------------------------------------------------
# Housekeeping
# ---------------------------------------------------------------------------


def pytest_sessionstart(session: pytest.Session) -> None:
    # Start each run with a clean artifacts dir so old failure evidence
    # doesn't get mistaken for this run's.
    if ARTIFACTS_DIR.exists():
        shutil.rmtree(ARTIFACTS_DIR)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
