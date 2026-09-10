from __future__ import annotations

from playwright.sync_api import Page

from framework.pages.base_page import BasePage


class CartPage(BasePage):
    path = "/cart.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.cart_items = page.locator(".cart_item")
        self.checkout_button = page.get_by_role("button", name="Checkout")

    def item_names(self) -> list[str]:
        return self.page.locator(".inventory_item_name").all_inner_texts()

    def checkout(self) -> "CartPage":
        self.click(self.checkout_button)
        return self
