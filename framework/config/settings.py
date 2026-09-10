"""
Central config for the framework.

Every environment-specific value (base URLs, credentials, timeouts) lives
here and is resolved from environment variables, never hardcoded in a test
or page object. This is what lets the exact same test suite run against
dev/staging/prod (or, here, against two unrelated public targets) just by
swapping env vars — that's the actual definition of "config-driven," not
a settings.py file that still hardcodes one URL.

Usage:
    from framework.config.settings import settings
    page.goto(settings.ui_base_url)
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Load the environment-specific .env file if present, e.g. ENV=staging -> .env.staging
_env_name = os.getenv("ENV", "dev")
_env_file = ROOT_DIR / f".env.{_env_name}"
if _env_file.exists():
    load_dotenv(_env_file)
else:
    # fall back to a generic .env for local dev
    load_dotenv(ROOT_DIR / ".env")


def _bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    env: str = field(default_factory=lambda: os.getenv("ENV", "dev"))

    # --- UI target (SauceDemo) ---
    ui_base_url: str = field(
        default_factory=lambda: os.getenv("UI_BASE_URL", "https://www.saucedemo.com")
    )
    ui_username: str = field(default_factory=lambda: os.getenv("UI_USERNAME", "standard_user"))
    ui_password: str = field(default_factory=lambda: os.getenv("UI_PASSWORD", "secret_sauce"))

    # --- API target (reqres.in) ---
    api_base_url: str = field(
        default_factory=lambda: os.getenv("API_BASE_URL", "https://reqres.in")
    )
    api_key: str = field(default_factory=lambda: os.getenv("API_KEY", "reqres-free-v1"))

    # --- Playwright / execution behavior ---
    headless: bool = field(default_factory=lambda: _bool("HEADLESS", True))
    default_timeout_ms: int = field(default_factory=lambda: int(os.getenv("TIMEOUT_MS", "10000")))
    slow_mo_ms: int = field(default_factory=lambda: int(os.getenv("SLOW_MO_MS", "0")))

    # --- Storage / artifacts ---
    auth_storage_dir: Path = field(default_factory=lambda: ROOT_DIR / ".auth")
    baseline_screenshot_dir: Path = field(
        default_factory=lambda: ROOT_DIR / "tests" / "visual" / "baselines"
    )


settings = Settings()
