"""Login flow: happy path + data-driven negative cases."""
import json

import pytest

from framework.config.settings import settings
from framework.pages.login_page import LoginPage
from framework.utils.data_loader import load_json

NEGATIVE_CASES = load_json("login_users.json")


@pytest.mark.smoke
def test_standard_user_can_log_in(page):
    login_page = LoginPage(page).goto()
    login_page.login(settings.ui_username, settings.ui_password)
    page.wait_for_url("**/inventory.html")
    assert "inventory.html" in page.url


@pytest.mark.regression
@pytest.mark.parametrize("case", NEGATIVE_CASES, ids=[c["case"] for c in NEGATIVE_CASES])
def test_login_negative_cases(page, case):
    login_page = LoginPage(page).goto()
    login_page.login(case["username"], case["password"])
    assert case["expected_error"] in login_page.error_text()
