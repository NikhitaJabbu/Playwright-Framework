"""
Cart + checkout flow. Uses the `authenticated_page` fixture (storageState
reuse from conftest.py) instead of logging in inside every test -- these
tests start already-authenticated, on the inventory page.
"""
import pytest

from framework.pages.cart_page import CartPage
from framework.pages.checkout_page import (
    CheckoutCompletePage,
    CheckoutStepOnePage,
    CheckoutStepTwoPage,
)
from framework.pages.inventory_page import InventoryPage
from framework.utils.data_loader import load_json

CHECKOUT_VALIDATION_CASES = load_json("checkout_validation.json")


@pytest.mark.smoke
def test_add_item_updates_cart_badge(authenticated_page):
    page = authenticated_page
    inventory = InventoryPage(page).goto()
    assert inventory.cart_count() == 0

    inventory.add_to_cart("Sauce Labs Backpack")
    assert inventory.cart_count() == 1

    inventory.remove_from_cart("Sauce Labs Backpack")
    assert inventory.cart_count() == 0


@pytest.mark.smoke
def test_full_checkout_happy_path(authenticated_page):
    page = authenticated_page
    inventory = InventoryPage(page).goto()
    inventory.add_to_cart("Sauce Labs Backpack")
    inventory.add_to_cart("Sauce Labs Bike Light")
    inventory.go_to_cart()

    cart = CartPage(page)
    assert set(cart.item_names()) == {"Sauce Labs Backpack", "Sauce Labs Bike Light"}
    cart.checkout()

    step_one = CheckoutStepOnePage(page)
    step_one.fill_info("Nikky", "Jabbu", "62025")

    step_two = CheckoutStepTwoPage(page)
    assert "Total" in step_two.total_text()
    step_two.finish()

    complete = CheckoutCompletePage(page)
    assert "Thank you" in complete.confirmation_text()


@pytest.mark.regression
@pytest.mark.parametrize(
    "case", CHECKOUT_VALIDATION_CASES, ids=[c["case"] for c in CHECKOUT_VALIDATION_CASES]
)
def test_checkout_requires_all_fields(authenticated_page, case):
    page = authenticated_page
    inventory = InventoryPage(page).goto()
    inventory.add_to_cart("Sauce Labs Backpack")
    inventory.go_to_cart()
    CartPage(page).checkout()

    step_one = CheckoutStepOnePage(page)
    step_one.fill_info(case["first"], case["last"], case["postal"])
    assert case["expected_error"] in step_one.error_text()


@pytest.mark.regression
def test_sort_price_low_to_high(authenticated_page):
    inventory = InventoryPage(authenticated_page).goto()
    inventory.sort_by("Price (low to high)")
    prices = inventory.item_prices()
    assert prices == sorted(prices)
