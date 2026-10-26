import os

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from tests.pages.dashboard_page import DashboardPage
from tests.pages.login_page import LoginPage
from tests.pages.unit_page import UnitPage


@pytest.mark.smoke
def test_student_can_open_first_unit_and_see_key_ideas(
    prepared_driver: WebDriver,
    base_url: str,
) -> None:
    login_page = LoginPage(prepared_driver, base_url)
    login_page.open()
    login_page.login(
        os.getenv("E2E_STUDENT_EMAIL", "demo@example.com"),
        os.getenv("E2E_STUDENT_PASSWORD", "q1w2e3r4"),
    )
    dashboard_page = DashboardPage(prepared_driver)
    dashboard_page.wait_until_opened()
    dashboard_page.should_be_visible()

    unit_page = UnitPage(prepared_driver)
    unit_page.open_first_unit()
    unit_page.should_show_overview()
    unit_page.open_key_ideas()
    unit_page.should_show_key_ideas()
    unit_page.should_have_progress(percentage=19, completed_sections=2, total_sections=14)
