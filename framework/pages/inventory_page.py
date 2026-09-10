from __future__ import annotations

from playwright.sync_api import Page

from framework.pages.base_page import BasePage


class InventoryPage(BasePage):
    path = "/inventory.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.inventory_items = page.locator(".inventory_item")
        self.cart_badge = page.locator(".shopping_cart_badge")
        self.cart_link = page.locator(".shopping_cart_link")
        self.sort_dropdown = page.locator("[data-test='product-sort-container']")

    def item_count(self) -> int:
        return self.inventory_items.count()

    def add_to_cart(self, product_name: str) -> "InventoryPage":
        item = self.page.locator(".inventory_item").filter(has_text=product_name)
        item.get_by_role("button", name="Add to cart").click()
        return self

    def remove_from_cart(self, product_name: str) -> "InventoryPage":
        item = self.page.locator(".inventory_item").filter(has_text=product_name)
        item.get_by_role("button", name="Remove").click()
        return self

    def cart_count(self) -> int:
        if not self.is_visible(self.cart_badge):
            return 0
        return int(self.text_of(self.cart_badge))

    def go_to_cart(self) -> "InventoryPage":
        self.click(self.cart_link)
        return self

    def sort_by(self, label: str) -> "InventoryPage":
        self.sort_dropdown.select_option(label=label)
        return self

    def item_prices(self) -> list[float]:
        raw = self.page.locator(".inventory_item_price").all_inner_texts()
        return [float(p.replace("$", "")) for p in raw]
