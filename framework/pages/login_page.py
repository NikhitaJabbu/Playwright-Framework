from __future__ import annotations

from playwright.sync_api import Page

from framework.pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/"

    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = page.get_by_placeholder("Username")
        self.password_input = page.get_by_placeholder("Password")
        self.login_button = page.get_by_role("button", name="Login")
        self.error_message = page.locator("[data-test='error']")

    def login(self, username: str, password: str) -> "LoginPage":
        self.fill(self.username_input, username)
        self.fill(self.password_input, password)
        self.click(self.login_button)
        return self

    def error_text(self) -> str:
        return self.text_of(self.error_message)
