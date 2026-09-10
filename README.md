# Playwright Test Framework

[![CI](https://github.com/NikhitaJabbu/playwright-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/NikhitaJabbu/playwright-framework/actions/workflows/ci.yml)

> Badge above assumes this repo is pushed to `NikhitaJabbu/playwright-framework`.
> Update the path once you pick a real repo name — it won't render until then.

A Python + Playwright automation framework, exercised against two unrelated
public targets (a UI demo app and a public REST API) to prove the
architecture is reusable rather than hardcoded to one site's quirks.

- **UI target:** [SauceDemo](https://www.saucedemo.com) — login, cart, checkout
- **API target:** [reqres.in](https://reqres.in) — CRUD user endpoints

The thing being demonstrated here isn't "I can write Playwright scripts,"
it's framework ownership: Page Object Model with a shared base class,
config-driven environments, auth-session reuse, data-driven tests, network
mocking, visual regression, cross-browser CI with retry and failure
artifacts, and a container build. Each of those is a separate, real
engineering decision, documented below with the reasoning behind it.

## Why Python, not TypeScript

Playwright's Python bindings are a first-class SDK, not a wrapper —
`sync_api`/`async_api` map onto the same underlying protocol as the JS
library. One real gap: Playwright Test's `expect(page).to_have_screenshot()`
snapshot assertion is a Playwright *Test runner* feature (JS/TS only) and
doesn't exist in `playwright.sync_api`. This framework's visual regression
suite (`tests/visual/`) implements that piece manually with Pillow —
see `framework/utils/visual_compare.py` for why and how.

## Architecture

```
framework/
  config/settings.py    # env-var-driven config, one Settings object, no
                         # hardcoded URLs anywhere else in the codebase
  pages/                # Page Object Model: base_page.py + one file per
                         # SauceDemo page
  api/reqres_client.py  # same idea as a page object, for the API target
  fixtures/             # (reserved for fixtures shared beyond conftest.py)
  utils/
    data_loader.py       # JSON/YAML test data loading
    visual_compare.py    # manual pixel-diff visual regression

tests/
  ui/            # SauceDemo tests (Page Object Model)
  api/           # reqres.in tests (APIRequestContext)
  visual/        # visual regression + baselines/
  data/          # JSON fixtures consumed by parametrized tests

conftest.py      # markers, storageState auth reuse, tracing/screenshot-
                 # on-failure -- this file is what turns "a folder of
                 # scripts" into a framework;
```

### Config-driven environments

Nothing in `tests/` or `framework/pages/` references a URL, username, or
timeout directly. Everything goes through `framework/config/settings.py`,
which resolves from environment variables (loaded from `.env.<ENV>`, e.g.
`.env.dev` / `.env.staging`). Switching targets is:

```bash
ENV=staging pytest
```

not a find-and-replace across test files. `.env.staging` in this repo
points at the same public target with a different demo user, only to prove
the mechanism — in a real project it would point at an actual staging
deployment.

### Auth session reuse (storageState)

`conftest.py`'s `auth_storage_state_path` fixture logs in **once per test
session**, saves Playwright's `storageState` to disk, and every test that
needs a logged-in session uses the `authenticated_page` fixture instead of
running the login flow itself. This is the single highest-leverage
perf/flake fix available in UI automation - login is usually the least
stable, slowest part of a test, and re-running it in every test multiplies
both problems by test count.

### Data-driven tests

`tests/data/*.json` holds parametrize inputs (`tests/ui/test_login.py`,
`test_cart_and_checkout.py`). Adding a new negative-login case or a new
checkout-validation case is a JSON edit, not a new test function.

### Tags: smoke vs regression

```bash
pytest -m smoke        # fast, critical-path only -- what should gate a PR
pytest -m regression   # full coverage -- what should run nightly
pytest -m api          # API suite only, no browser needed
pytest -m visual       # visual regression only
```

Markers are registered in `conftest.py::pytest_configure` (`--strict-markers`
in `pytest.ini` means a typo'd marker fails loudly instead of silently
matching nothing).

### Network interception/mocking

`tests/ui/test_network_mocking.py` uses `page.route()` to simulate
conditions the real target site will never hand you on demand: broken
product images, a dead stylesheet CDN. Every intercept asserts its own
call count (`len(intercepted_urls) > 0`) — a mocked route that never
actually fires is a silent no-op test, and that assertion is what catches
it if the URL pattern stops matching after a site change.

### Visual regression

`tests/visual/` screenshots the login and inventory pages and diffs them
against `tests/visual/baselines/*.png` with Pillow
(`framework/utils/visual_compare.py`). First run with no baseline present
records one and passes. A real UI change means deleting
the stale baseline and re-recording deliberately, not silencing a real
diff.

```bash
# seed/refresh baselines locally, then commit the PNGs
rm tests/visual/baselines/*.png
pytest tests/visual
```

### Trace and screenshot on failure only

`conftest.py` starts Playwright tracing for every test but only *keeps*
the trace zip (and takes a failure screenshot) when the test actually
fails — passing tests don't bloat `test-results/` or CI artifact storage.
Open a trace with:

```bash
playwright show-trace test-results/artifacts/<test-name>-trace.zip
```

## Running locally

```bash
pip install -r requirements.txt
python -m playwright install --with-deps chromium firefox webkit

pytest                      # everything
pytest -m smoke             # fast path
pytest tests/ui             # UI suite only
pytest tests/api            # API suite only
pytest --browser firefox    # run against a specific engine
pytest -n auto              # parallelize across CPU cores (pytest-xdist)
```

## CI (`.github/workflows/ci.yml`)

- Matrix run across **chromium / firefox / webkit**, `fail-fast: false` so
  one engine's failure doesn't hide results from the other two.
- `pytest-rerunfailures` retries a failing test twice before it's counted
  as failed — absorbs transient network flake without hiding a real,
  reproducible bug (a test that only ever passes on retry is still worth
  investigating separately).
- On failure: traces, failure screenshots, and visual diffs are uploaded
  as build artifacts (`actions/upload-artifact`), plus a JUnit XML report
  every run.
- A separate `docker` job builds the image and runs the smoke suite
  inside the container on every push — catches "works on my machine but
  the Docker image is broken" before it reaches anyone.
- Runs on push, PR, `workflow_dispatch` (with a marker input, so you can
  manually fire `regression` or `visual` from the Actions tab), and a
  nightly cron — the nightly run is what catches the *target site*
  changing underneath the suite, independent of any change to this repo.
- Cross-browser visual regression is a known, explicit gap: baselines here
  are Chromium-only, because rendering differs enough per-engine that a
  real cross-browser visual suite needs per-browser baseline sets, which
  is out of scope for this project.

## Docker

```bash
docker build -t playwright-framework .
docker run --rm playwright-framework                    # runs @smoke
docker run --rm playwright-framework pytest -m regression
docker compose run tests                                 # full suite, artifacts mounted to ./test-results
```

Built on `mcr.microsoft.com/playwright/python`, which ships all three
browser engines and their OS dependencies preinstalled — building this on
a bare `python:3.11` image means separately `apt install`-ing ~30 browser
dependency packages by hand, which is the step most Docker+Playwright
write-ups skip.

## Adding a new test

1. **New page under test?** Add a page object in `framework/pages/`
   inheriting `BasePage`, expose locators in `__init__`, actions as
   methods that return `self` where it reads naturally as a chain.
2. **New test data?** Add a case to the relevant JSON file in
   `tests/data/`, not inline in the test function.
3. **New test?** Put it under `tests/ui/`, `tests/api/`, or `tests/visual/`
   and tag it `@pytest.mark.smoke` or `@pytest.mark.regression` (or both
   `api`/`visual` alongside).
4. Run it locally against `HEADLESS=false` to watch it, e.g.:
   `HEADLESS=false pytest tests/ui/test_login.py -v`

## Known limitations

- Visual baselines are Chromium-only (see CI section above).
- The API suite targets reqres.in's public free tier, which is rate-limited
  and occasionally returns `403` under heavy anonymous traffic — this is a
  target-side constraint, not a framework defect. `API_KEY` in `.env.dev`
  uses the documented free-tier key.
- No parallel cross-target run (UI + API) is wired into one CI job by
  design — they're kept as separate marker-selectable suites so either can
  run independently without waiting on the other.
