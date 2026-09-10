"""
Thin client wrapping Playwright's APIRequestContext for reqres.in.

This is the API-side equivalent of a page object: tests never build raw
URLs or headers themselves, they call methods here. It's what makes the
API suite a first-class part of the *same* framework instead of a bolt-on
folder of requests calls -- it shares config (framework/config/settings.py)
and the same "tests don't know about wire details" discipline as the UI
page objects.
"""
from __future__ import annotations

from playwright.sync_api import APIRequestContext

from framework.config.settings import settings


class ReqresClient:
    def __init__(self, request_context: APIRequestContext):
        self._rc = request_context

    def list_users(self, page: int = 1):
        return self._rc.get(f"{settings.api_base_url}/api/users", params={"page": page})

    def get_user(self, user_id: int):
        return self._rc.get(f"{settings.api_base_url}/api/users/{user_id}")

    def create_user(self, name: str, job: str):
        return self._rc.post(
            f"{settings.api_base_url}/api/users",
            data={"name": name, "job": job},
        )

    def update_user(self, user_id: int, name: str, job: str):
        return self._rc.put(
            f"{settings.api_base_url}/api/users/{user_id}",
            data={"name": name, "job": job},
        )

    def delete_user(self, user_id: int):
        return self._rc.delete(f"{settings.api_base_url}/api/users/{user_id}")

    def register(self, email: str, password: str):
        return self._rc.post(
            f"{settings.api_base_url}/api/register",
            data={"email": email, "password": password},
        )
