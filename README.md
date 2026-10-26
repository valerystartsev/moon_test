# Student authentication UI tests

Pytest + Selenium + Page Object Model with remote browser execution through Moon/Selenoid-compatible endpoint.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configure

Copy `.env.example` to `.env` and set the application and Moon URLs:

```bash
cp .env.example .env
```

The test reads environment variables directly. A `.env` file is also loaded automatically by `tests/conftest.py`.

## Run

```bash
pytest -m smoke -v
```

Run the two scenarios in parallel:

```bash
python -m pytest -n 2 --dist=load -m smoke -v
```

Use `-n 4` when the suite grows and the browser server has sufficient capacity.
With two tests, at most two workers execute tests concurrently.

## Shared authentication

Each run performs one UI login in a temporary browser. After Dashboard opens and
application storage initializes, the controller sends an in-memory snapshot of
cookies, localStorage and sessionStorage to every xdist worker. The bootstrap
browser closes before test browsers start. No token snapshot is written to disk.

Every test requests `authenticated_driver`, gets a fresh remote browser, restores
its own copy of the snapshot, and opens Dashboard without submitting the login
form again. Sequential execution uses the same one-login setup. `--collect-only`
does not create browsers or log in. The terminal reports completion of the single
bootstrap login. Session IDs and worker IDs are available in JUnit test properties
when using `--junitxml=artifacts/results.xml`.

Snapshot reuse applies only within one run. A rejected or expired session fails
setup explicitly; there is no automatic login retry. Local progress changes remain
isolated between browsers; server-side changes still affect the shared account.
The Dashboard and Unit 1 assertions retain their existing expected progress.
This suite checks authenticated pages; the form login is validated during setup.

Check collection without opening a browser:

```bash
python -m pytest --collect-only -q
```

Run against Firefox:

```bash
BROWSER_NAME=firefox pytest -m smoke -v
```

## Project layout

```text
tests/
├── conftest.py
├── pages/
│   ├── dashboard_page.py
│   └── login_page.py
└── test_student_authentication.py
```

## Notes

- The test sets `adaptation_onboarding_done` in `localStorage` before opening `/login`.
- Each test gets a fresh remote browser session.
- Screenshots are saved to `artifacts/screenshots` after setup or test failures; names include the worker ID. The authentication bootstrap has a separate setup screenshot.
- The endpoint is expected to be compatible with Moon/Selenoid and accept `selenoid:options`.
- Do not commit `.env`, because it may contain credentials.

## Authentication setup checks

Run the coordination checks without Moon or application access:

```bash
python -m pytest tests/test_shared_auth.py -q
```

These cover one login across workers and worker replacement, independent snapshot
copies, collect-only, rejected snapshots, origin validation and redacted diagnostics.
