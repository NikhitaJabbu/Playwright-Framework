from __future__ import annotations

from playwright.sync_api import Page

from framework.pages.base_page import BasePage


class CheckoutStepOnePage(BasePage):
    path = "/checkout-step-one.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.first_name = page.locator("[data-test='firstName']")
        self.last_name = page.locator("[data-test='lastName']")
        self.postal_code = page.locator("[data-test='postalCode']")
        self.continue_button = page.get_by_role("button", name="Continue")
        self.error_message = page.locator("[data-test='error']")

    def fill_info(self, first: str, last: str, postal: str) -> "CheckoutStepOnePage":
        self.fill(self.first_name, first)
        self.fill(self.last_name, last)
        self.fill(self.postal_code, postal)
        self.click(self.continue_button)
        return self

    def error_text(self) -> str:
        return self.text_of(self.error_message)


class CheckoutStepTwoPage(BasePage):
    path = "/checkout-step-two.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.finish_button = page.get_by_role("button", name="Finish")
        self.summary_total = page.locator(".summary_total_label")
        self.item_totals = page.locator(".summary_subtotal_label")

    def finish(self) -> "CheckoutStepTwoPage":
        self.click(self.finish_button)
        return self

    def total_text(self) -> str:
        return self.text_of(self.summary_total)


class CheckoutCompletePage(BasePage):
    path = "/checkout-complete.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.complete_header = page.locator(".complete-header")

    def confirmation_text(self) -> str:
        return self.text_of(self.complete_header)
