import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from tests.pages.unit_page import UnitPage


@pytest.mark.smoke
def test_student_can_open_first_unit_and_see_key_ideas(
    authenticated_driver: WebDriver,
) -> None:
    unit_page = UnitPage(authenticated_driver)
    unit_page.open_first_unit()
    unit_page.should_show_overview()
    unit_page.open_key_ideas()
    unit_page.should_show_key_ideas()
    unit_page.should_have_progress(percentage=19, completed_sections=2, total_sections=14)
