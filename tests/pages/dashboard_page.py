import re
from time import monotonic

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class DashboardPage:
    PAGE_HEADING = (
        By.XPATH,
        "//*[self::h1 or self::h2 or self::h3]"
        "[contains(normalize-space(), 'Course Dashboard')]",
    )
    COURSE_TITLE = (
        By.XPATH,
        "//*[contains(normalize-space(), 'Business English — Adaptation')]",
    )

    def __init__(self, driver: WebDriver, timeout: int = 30):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def wait_until_opened(self) -> None:
        self.wait.until(lambda driver: re.search(r"/dashboard$", driver.current_url) is not None)

    def should_be_visible(self) -> None:
        self.wait.until(EC.visibility_of_element_located(self.PAGE_HEADING))
        self.wait.until(EC.visibility_of_element_located(self.COURSE_TITLE))

    def should_have_progress(
        self,
        course_progress: int,
        words_learned: int,
        total_words: int,
        timeout: int = 60,
    ) -> None:
        expected = {
            "Course Progress": f"{course_progress}%",
            "Words Learned": f"{words_learned} of {total_words}",
        }
        actual: dict[str, str] = {}
        matched_since: float | None = None

        def counters_have_settled(driver: WebDriver) -> bool:
            nonlocal matched_since
            try:
                for label in expected:
                    locator = (
                        By.XPATH,
                        f"//button[.//p[normalize-space()='{label}']]"
                        "//span[contains(concat(' ', normalize-space(@class), ' '),"
                        " ' count-up-number ')]/parent::div",
                    )
                    # Resolve again on every poll: rendering may replace the counter.
                    value = driver.find_element(*locator)
                    if not value.is_displayed():
                        matched_since = None
                        return False
                    actual[label] = " ".join(value.text.split())
            except StaleElementReferenceException:
                matched_since = None
                return False

            if actual != expected:
                matched_since = None
                return False
            if matched_since is None:
                matched_since = monotonic()
            # Require both final values to persist beyond a single animation frame.
            return monotonic() - matched_since >= 0.5

        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.2).until(
                counters_have_settled
            )
        except TimeoutException as error:
            raise AssertionError(
                f"Dashboard counters did not settle within {timeout}s: "
                f"expected {expected!r}, got {actual!r}"
            ) from error
