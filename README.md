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

Run four sessions in parallel:

```bash
pytest -n 4 -m smoke -v
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
- Screenshots are saved to `artifacts/screenshots` after a test failure.
- The endpoint is expected to be compatible with Moon/Selenoid and accept `selenoid:options`.
- Do not commit `.env`, because it may contain credentials.
