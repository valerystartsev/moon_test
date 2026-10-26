import os

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from tests.pages.dashboard_page import DashboardPage
from tests.pages.login_page import LoginPage


@pytest.mark.smoke
def test_student_can_login_and_open_dashboard(
    prepared_driver: WebDriver,
    base_url: str,
) -> None:
    student_email = os.getenv("E2E_STUDENT_EMAIL", "demo@example.com")
    student_password = os.getenv("E2E_STUDENT_PASSWORD", "q1w2e3r4")

    login_page = LoginPage(prepared_driver, base_url)
    dashboard_page = DashboardPage(prepared_driver)

    login_page.open()
    login_page.login(student_email, student_password)

    dashboard_page.wait_until_opened()
    dashboard_page.should_be_visible()
    dashboard_page.should_have_progress(
        course_progress=9, words_learned=16, total_words=129
    )
