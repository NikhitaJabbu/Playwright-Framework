"""
Visual regression via manual pixel-diff comparison (see
framework/utils/visual_compare.py) against a baseline stored in
tests/visual/baselines/.

Note: Playwright's `expect(page).to_have_screenshot(...)` is a JS/TS-only
Playwright Test feature and does not exist in Python's playwright.sync_api
-- this suite implements the equivalent manually with Pillow rather than
call an API that isn't there.

First run: baselines don't exist yet, so the test records them and
passes. Delete a baseline PNG and re-run to force re-recording after an
intentional UI change. CI runs against the committed baselines, so any
unintended pixel drift beyond the threshold fails the build and uploads
the diff image as an artifact (see .github/workflows/ci.yml).
"""
import pytest

from framework.pages.inventory_page import InventoryPage
from framework.pages.login_page import LoginPage
from framework.utils.visual_compare import assert_matches_baseline


@pytest.mark.visual
def test_login_page_visual_baseline(page):
    LoginPage(page).goto()
    assert_matches_baseline(page, "login_page")


@pytest.mark.visual
def test_inventory_page_visual_baseline(page):
    login_page = LoginPage(page).goto()
    login_page.login("standard_user", "secret_sauce")
    page.wait_for_url("**/inventory.html")
    InventoryPage(page)
    assert_matches_baseline(page, "inventory_page")
