import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from tests.pages.dashboard_page import DashboardPage


@pytest.mark.smoke
def test_student_can_view_dashboard(authenticated_driver: WebDriver) -> None:
    dashboard_page = DashboardPage(authenticated_driver)
    dashboard_page.should_be_visible()
    dashboard_page.should_have_progress(
        course_progress=9, words_learned=16, total_words=129
    )
