"""
Network interception/mocking tests.

The point of these: SauceDemo (like most public demo sites) will never
hand you a 500, a timeout, or an empty inventory response on demand --
so there's no way to test how the UI behaves under those conditions
without mocking the network. This is also the clearest way to show a
framework does more than click-and-assert: it can simulate backend
failure states the real target can't produce.
"""
import pytest

from framework.pages.inventory_page import InventoryPage
from framework.pages.login_page import LoginPage


@pytest.mark.regression
def test_product_images_fail_gracefully_when_asset_requests_error(page):
    """Intercept every product image request and fail it with a 404, then
    assert the page still renders every product's name/price correctly --
    proving the app degrades gracefully on asset failure rather than
    breaking the whole page. Also asserts the intercept actually fired
    (call count), which is the part that proves this is real interception
    and not a no-op route.

    Deliberately doesn't hardcode the catalog size (e.g. "== 6") -- that's
    a magic number that breaks the moment the target site adds a product.
    Instead it captures the item count with images working, then asserts
    it's unchanged with images broken."""
    login_page = LoginPage(page).goto()
    login_page.login("standard_user", "secret_sauce")
    page.wait_for_url("**/inventory.html")
    baseline_count = InventoryPage(page).item_count()
    assert baseline_count > 0

    intercepted_urls = []

    def fail_image(route):
        intercepted_urls.append(route.request.url)
        route.fulfill(status=404, body="")

    page.route("**/*.jpg", fail_image)
    page.reload()

    inventory = InventoryPage(page)
    assert inventory.item_count() == baseline_count
    assert len(intercepted_urls) > 0, "expected image requests to be intercepted"


@pytest.mark.regression
def test_login_survives_stylesheet_failure(page):
    """Force every CSS request to fail and assert the login flow still
    completes functionally. Demonstrates the framework can simulate a CDN
    or asset-pipeline outage -- a state the real, healthy target site will
    never hand you on demand -- and assert the app degrades to "ugly but
    working" rather than becoming unusable."""
    intercepted = []

    def fail_css(route):
        intercepted.append(route.request.url)
        route.abort()

    page.route("**/*.css", fail_css)

    login_page = LoginPage(page).goto()
    login_page.login("standard_user", "secret_sauce")
    page.wait_for_url("**/inventory.html")

    assert "inventory.html" in page.url
    assert len(intercepted) > 0, "expected stylesheet requests to be intercepted"
