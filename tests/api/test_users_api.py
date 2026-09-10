"""
API suite against reqres.in, using Playwright's own APIRequestContext
(via `request` from pytest-playwright) rather than a separate HTTP
library. This is the part of the framework that proves the architecture
isn't hardcoded to one target: same config module, same
markers/CI/reporting, completely different protocol.

reqres.in's free tier requires an x-api-key header as of 2025 -- handled
once in this fixture, not per test.
"""
import pytest

from framework.api.reqres_client import ReqresClient
from framework.config.settings import settings


@pytest.fixture
def api_client(playwright):
    request_context = playwright.request.new_context(
        extra_http_headers={"x-api-key": settings.api_key}
    )
    yield ReqresClient(request_context)
    request_context.dispose()


@pytest.mark.api
@pytest.mark.smoke
def test_list_users_returns_paginated_data(api_client):
    response = api_client.list_users(page=2)
    assert response.ok
    body = response.json()
    assert body["page"] == 2
    assert len(body["data"]) > 0
    assert "email" in body["data"][0]


@pytest.mark.api
@pytest.mark.smoke
def test_get_single_user(api_client):
    response = api_client.get_user(2)
    assert response.ok
    body = response.json()
    assert body["data"]["id"] == 2
    assert "@" in body["data"]["email"]


@pytest.mark.api
@pytest.mark.regression
def test_get_nonexistent_user_returns_404(api_client):
    response = api_client.get_user(999)
    assert response.status == 404


@pytest.mark.api
@pytest.mark.regression
def test_create_user(api_client):
    response = api_client.create_user(name="Nikky Jabbu", job="SDET")
    assert response.status == 201
    body = response.json()
    assert body["name"] == "Nikky Jabbu"
    assert body["job"] == "SDET"
    assert "id" in body


@pytest.mark.api
@pytest.mark.regression
def test_update_user(api_client):
    response = api_client.update_user(2, name="Nikky Jabbu", job="Software Engineer")
    assert response.ok
    body = response.json()
    assert body["job"] == "Software Engineer"


@pytest.mark.api
@pytest.mark.regression
def test_delete_user_returns_204(api_client):
    response = api_client.delete_user(2)
    assert response.status == 204


@pytest.mark.api
@pytest.mark.regression
def test_register_without_password_is_rejected(api_client):
    response = api_client.register(email="eve.holt@reqres.in", password="")
    assert response.status == 400
    assert "error" in response.json()
