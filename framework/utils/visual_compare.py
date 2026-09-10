"""
Manual pixel-diff visual regression.

Playwright's `expect(page).to_have_screenshot(...)` snapshot assertion is
a Playwright Test (JS/TS) feature -- it does NOT exist in the Python
`playwright.sync_api` library, and pytest-playwright (as of 0.9.0) doesn't
add it either. Anyone porting a JS Playwright framework to Python and
assuming that API exists will hit an AttributeError at collection time.

This module is the Python-side replacement: take a screenshot, compare it
pixel-by-pixel against a stored baseline with Pillow, and fail with a
percentage diff (plus a saved diff image) when the mismatch exceeds a
threshold.

Usage:
    from framework.utils.visual_compare import assert_matches_baseline
    assert_matches_baseline(page, "login_page")
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import Page

from framework.config.settings import settings

DIFF_DIR = Path(__file__).resolve().parent.parent.parent / "test-results" / "visual-diffs"


def assert_matches_baseline(
    page: Page, name: str, max_diff_ratio: float = 0.02, full_page: bool = True
) -> None:
    """Compare the current page render against tests/visual/baselines/{name}.png.

    If no baseline exists yet, this call records one and passes (same
    "first run creates the baseline" convention as Playwright Test's own
    snapshot assertions) -- run once locally with a clean baselines dir to
    seed them, then commit the PNGs.
    """
    settings.baseline_screenshot_dir.mkdir(parents=True, exist_ok=True)
    DIFF_DIR.mkdir(parents=True, exist_ok=True)

    baseline_path = settings.baseline_screenshot_dir / f"{name}.png"
    actual_bytes = page.screenshot(full_page=full_page)

    if not baseline_path.exists():
        baseline_path.write_bytes(actual_bytes)
        return

    actual_path = DIFF_DIR / f"{name}-actual.png"
    actual_path.write_bytes(actual_bytes)

    baseline_img = Image.open(baseline_path).convert("RGB")
    actual_img = Image.open(actual_path).convert("RGB")

    if baseline_img.size != actual_img.size:
        raise AssertionError(
            f"visual regression [{name}]: dimensions changed "
            f"{baseline_img.size} -> {actual_img.size}"
        )

    diff = ImageChops.difference(baseline_img, actual_img)
    diff_pixels = sum(1 for px in diff.getdata() if px != (0, 0, 0))
    total_pixels = baseline_img.size[0] * baseline_img.size[1]
    diff_ratio = diff_pixels / total_pixels

    if diff_ratio > max_diff_ratio:
        diff_path = DIFF_DIR / f"{name}-diff.png"
        diff.save(diff_path)
        raise AssertionError(
            f"visual regression [{name}]: {diff_ratio:.2%} of pixels differ "
            f"(threshold {max_diff_ratio:.2%}). Diff saved to {diff_path}, "
            f"actual saved to {actual_path}."
        )
