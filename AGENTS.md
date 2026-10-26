# Repository Guidelines

## Project Structure & Module Organization

This repository contains Python UI tests for student authentication, using pytest, Selenium, and the Page Object Model. The application under test runs separately.

- `tests/test_student_authentication.py` contains the login smoke test.
- `tests/pages/` contains page objects that encapsulate locators and browser interactions.
- `tests/conftest.py` provides remote browser fixtures, onboarding preparation, and failure screenshots.
- `config/browsers.json` defines browser images; `docker-compose.yml` describes Moon and Moon UI services.
- `pytest.ini` defines test discovery and markers. Generated screenshots go in `artifacts/screenshots/`.

## Build, Test, and Development Commands

Run commands from the repository root. In PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set application and browser service settings in `.env` before running tests. Use an existing `.env` if already configured.

- `docker compose up -d`: start the configured Moon services when using the local setup.
- `python -m pytest --collect-only -q`: check test discovery without launching browser sessions.
- `python -m pytest -m smoke -v`: run critical authentication checks.
- `python -m pytest -n 4 -m smoke -v`: run with four workers; ensure browser capacity supports this.

## Coding Style & Naming Conventions

Follow existing Python style: four-space indentation, grouped imports, and type annotations for page methods and fixtures. Use `snake_case` for functions and modules, `PascalCase` for page classes, and `UPPER_CASE` for locator constants. Keep browser interactions in page objects and scenarios in test modules. Use explicit `WebDriverWait` conditions instead of fixed sleeps. No formatter or linter is currently configured.

## Testing Guidelines

Name test files `test_*.py` and functions `test_*`. Apply the registered `smoke` or `regression` markers as appropriate. Each test receives a fresh remote browser session. Authentication scenarios should use `prepared_driver` to initialize onboarding state. Review failure screenshots when diagnosing failures. No coverage threshold is configured; validate changed behavior against the target application and Moon-compatible endpoint.

## Commit & Pull Request Guidelines

Git history is unavailable in this checkout. Use concise, imperative commit subjects, such as `Add invalid-password login test`. PRs should describe changed behavior, relevant configuration, commands run, and results. Link related issues and attach screenshots when they clarify UI failures.

## Security & Configuration

Keep `.env`, credentials, and generated artifacts out of commits. Configure `BASE_URL`, `MOON_URL`, `E2E_STUDENT_EMAIL`, and `E2E_STUDENT_PASSWORD` through environment variables or `.env`; avoid hardcoding account secrets.
