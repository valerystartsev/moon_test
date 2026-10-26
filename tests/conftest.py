import os
from collections.abc import Generator
from copy import deepcopy

import pytest
from dotenv import load_dotenv
from selenium.webdriver.remote.webdriver import WebDriver

from tests.browser_session import (
    AuthSnapshot,
    capture_auth_state,
    create_browser,
    restore_auth_state,
    save_failure_screenshot,
)

load_dotenv()

AUTH_STATE = pytest.StashKey[dict]()
AUTH_ERROR = pytest.StashKey[str]()


def shared_auth_state(config: pytest.Config) -> dict:
    if AUTH_ERROR in config.stash:
        raise pytest.UsageError(config.stash[AUTH_ERROR])
    if AUTH_STATE not in config.stash:
        try:
            state = capture_auth_state(
                os.getenv("BASE_URL", "http://localhost:3000").rstrip("/"),
                os.getenv("MOON_URL", "http://localhost:4444/wd/hub"),
            )
        except Exception:
            # Do not repeat login on worker restart or include tokens in diagnostics.
            config.stash[AUTH_ERROR] = (
                "Shared authentication setup failed; no login retry was attempted. "
                "Check the application, Moon, credentials and "
                "artifacts/screenshots/controller-auth-bootstrap-setup.png."
            )
            raise pytest.UsageError(config.stash[AUTH_ERROR]) from None
        config.stash[AUTH_STATE] = state
        reporter = config.pluginmanager.getplugin("terminalreporter")
        if reporter is not None:
            reporter.write_line("Shared authentication: one UI login completed; snapshot kept in memory.")
    return config.stash[AUTH_STATE]


@pytest.hookimpl(optionalhook=True)
def pytest_configure_node(node) -> None:
    if not node.config.option.collectonly:
        node.workerinput["auth_state"] = deepcopy(shared_auth_state(node.config))


def pytest_unconfigure(config: pytest.Config) -> None:
    if AUTH_STATE in config.stash:
        del config.stash[AUTH_STATE]
    if hasattr(config, "workerinput"):
        config.workerinput.pop("auth_state", None)


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.getenv("BASE_URL", "http://localhost:3000").rstrip("/")


@pytest.fixture(scope="session")
def moon_url() -> str:
    return os.getenv("MOON_URL", "http://localhost:4444/wd/hub")


@pytest.fixture(scope="session")
def auth_state(pytestconfig: pytest.Config) -> AuthSnapshot:
    if hasattr(pytestconfig, "workerinput"):
        state = pytestconfig.workerinput.get("auth_state")
        if state is None:
            raise pytest.UsageError("Worker did not receive shared authentication; refusing to log in again")
        return AuthSnapshot(deepcopy(state))
    return AuthSnapshot(deepcopy(shared_auth_state(pytestconfig)))


@pytest.fixture
def driver(request: pytest.FixtureRequest, moon_url: str) -> Generator[WebDriver, None, None]:
    worker = os.getenv("PYTEST_XDIST_WORKER", "master")
    browser = create_browser(moon_url, f"{worker}-{request.node.name}")
    request.node.user_properties.append(("browser_session_id", browser.session_id))
    request.node.user_properties.append(("worker_id", worker))
    try:
        yield browser
    finally:
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


@pytest.fixture
def authenticated_driver(
    auth_state: AuthSnapshot, driver: WebDriver, base_url: str
) -> WebDriver:
    try:
        restore_auth_state(driver, auth_state, base_url)
    except Exception as error:
        # Keep storage and cookie values out of fixture failure tracebacks.
        raise RuntimeError(
            "Shared authentication could not open Dashboard; "
            f"no login retry was attempted ({type(error).__name__})"
        ) from None
    return driver


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    if report.failed and report.when in ("setup", "call"):
        browser = item.funcargs.get("driver")
        if browser is not None:
            worker = os.getenv("PYTEST_XDIST_WORKER", "master")
            save_failure_screenshot(browser, f"{worker}-{item.nodeid}-{report.when}")
