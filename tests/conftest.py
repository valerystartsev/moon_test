import os
from collections.abc import Generator
from pathlib import Path

import pytest
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver

load_dotenv()


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("BASE_URL", "http://localhost:3000").rstrip("/")


@pytest.fixture(scope="session")
def moon_url() -> str:
    return os.getenv("MOON_URL", "http://localhost:4444/wd/hub")


@pytest.fixture
def driver(moon_url: str) -> Generator[WebDriver, None, None]:
    options = Options()
    browser_version = os.getenv("BROWSER_VERSION")

    if browser_version:
        options.browser_version = browser_version

    options.platform_name = os.getenv("PLATFORM_NAME", "linux")
    options.set_capability("browserName", os.getenv("BROWSER_NAME", "chrome"))
    options.set_capability(
        "selenoid:options",
        {
            "name": os.getenv("TEST_NAME", "student-authentication"),
            "sessionTimeout": "5m",
            "enableVideo": os.getenv("MOON_ENABLE_VIDEO", "false").lower() == "true",
            "enableVNC": os.getenv("MOON_ENABLE_VNC", "false").lower() == "true",
            "enableLog": True,
        },
    )

    browser = webdriver.Remote(
        command_executor=moon_url,
        options=options,
    )
    browser.set_window_size(1440, 1000)

    yield browser

    browser.quit()


@pytest.fixture
def prepared_driver(driver: WebDriver, base_url: str) -> WebDriver:
    driver.get(base_url)
    driver.execute_script(
        "window.localStorage.setItem(arguments[0], arguments[1]);",
        "adaptation_onboarding_done",
        "1",
    )
    return driver


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.fixture(autouse=True)
def screenshot_on_failure(request: pytest.FixtureRequest, driver: WebDriver):
    yield

    report = getattr(request.node, "rep_call", None)
    if report is not None and report.failed:
        screenshots_dir = Path("artifacts/screenshots")
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        safe_name = request.node.nodeid.replace("/", "_").replace("::", "_")
        driver.save_screenshot(str(screenshots_dir / f"{safe_name}.png"))
