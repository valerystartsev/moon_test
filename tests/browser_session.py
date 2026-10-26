import os
from copy import deepcopy
from pathlib import Path
from time import monotonic
from urllib.parse import urlsplit

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from tests.pages.dashboard_page import DashboardPage
from tests.pages.login_page import LoginPage


class AuthSnapshot(dict):
    def __repr__(self) -> str:
        return "<AuthSnapshot: credentials redacted>"


def create_browser(moon_url: str, name: str) -> WebDriver:
    options = Options()
    if version := os.getenv("BROWSER_VERSION"):
        options.browser_version = version
    options.platform_name = os.getenv("PLATFORM_NAME", "linux")
    options.set_capability("browserName", os.getenv("BROWSER_NAME", "chrome"))
    options.set_capability(
        "selenoid:options",
        {
            "name": f"{os.getenv('TEST_NAME', 'student-authentication')}-{name}",
            "sessionTimeout": "5m",
            "enableVideo": os.getenv("MOON_ENABLE_VIDEO", "false").lower() == "true",
            "enableVNC": os.getenv("MOON_ENABLE_VNC", "false").lower() == "true",
            "enableLog": True,
        },
    )
    browser = webdriver.Remote(command_executor=moon_url, options=options)
    try:
        browser.set_window_size(1440, 1000)
    except Exception:
        browser.quit()
        raise
    return browser


def save_failure_screenshot(browser: WebDriver, name: str) -> None:
    # Screenshot errors must not hide the original test/setup failure.
    try:
        directory = Path("artifacts/screenshots")
        directory.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
        browser.save_screenshot(str(directory / f"{safe_name}.png"))
    except Exception:
        pass


def capture_auth_state(base_url: str, moon_url: str) -> dict:
    parsed = urlsplit(base_url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    browser = create_browser(moon_url, "auth-bootstrap")
    try:
        browser.get(origin)
        browser.execute_script(
            "localStorage.setItem('adaptation_onboarding_done', '1')"
        )
        login = LoginPage(browser, base_url)
        login.open()
        login.login(
            os.getenv("E2E_STUDENT_EMAIL", "demo@example.com"),
            os.getenv("E2E_STUDENT_PASSWORD", "q1w2e3r4"),
        )
        dashboard = DashboardPage(browser)
        dashboard.wait_until_opened()
        dashboard.should_be_visible()
        last_storage = None
        unchanged_since = monotonic()

        def storage_is_ready(driver: WebDriver) -> dict | bool:
            nonlocal last_storage, unchanged_since
            storage = driver.execute_script(
                "return {local: {...localStorage}, session: {...sessionStorage}}"
            )
            local = storage["local"]
            has_auth = any(
                key.startswith("sb-") and key.endswith("-auth-token")
                and local[key] and local[key] != "null"
                for key in local
            )
            has_progress = any(key.startswith("adaptation_progress_") for key in local)
            if not has_auth or not has_progress or storage != last_storage:
                last_storage = storage
                unchanged_since = monotonic()
                return False
            return storage if monotonic() - unchanged_since >= 1 else False

        storage = WebDriverWait(browser, 60, poll_frequency=0.2).until(
            storage_is_ready,
            message="Authentication and progress storage did not finish initializing",
        )
        return {"origin": origin, "cookies": browser.get_cookies(), **storage}
    except Exception:
        save_failure_screenshot(browser, "controller-auth-bootstrap-setup")
        raise
    finally:
        browser.quit()


def restore_auth_state(browser: WebDriver, state: dict, base_url: str) -> None:
    parsed = urlsplit(base_url)
    if state["origin"] != f"{parsed.scheme}://{parsed.netloc}":
        raise RuntimeError("Authentication snapshot belongs to another origin")
    browser.get(state["origin"])
    browser.delete_all_cookies()
    for cookie in state["cookies"]:
        browser.add_cookie(deepcopy(cookie))
    browser.execute_script(
        "localStorage.clear(); sessionStorage.clear();"
        "for (const [k,v] of Object.entries(arguments[0])) localStorage.setItem(k,v);"
        "for (const [k,v] of Object.entries(arguments[1])) sessionStorage.setItem(k,v);",
        state["local"],
        state["session"],
    )
    browser.get(f"{base_url}/dashboard")
    dashboard = DashboardPage(browser)
    dashboard.wait_until_opened()
    dashboard.should_be_visible()
