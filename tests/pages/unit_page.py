from urllib.parse import urlparse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class UnitPage:
    UNIT_NUMBER = 1
    TITLE = "Markets & Monopolies"
    SUBTITLE = "How buyers, sellers, and companies shape the economy"
    INTRODUCTION = (
        "Learn key business terms about markets, competition, and monopolies. "
        "Understand how companies compete and what happens when one company controls everything."
    )
    TABS = (
        "Intro", "Key Ideas", "Market Types", "Dictionary", "Comics",
        "Reading", "Questions", "Media Lab", "Media Quest", "Crossword",
        "Complaint Path", "Dialogue",
    )
    DEFINITIONS = (
        ("Market", "A place where buyers and sellers meet to trade goods and services."),
        ("Competition", "Companies fight to get customers by offering better products or lower prices."),
        ("Monopoly", "One company controls the whole market. There is no competition."),
    )
    KEY_IDEAS_TAB = (
        By.CSS_SELECTOR,
        "main a[href='#section-keyideas']",
    )

    def __init__(self, driver: WebDriver, timeout: int = 30):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def open(self) -> None:
        path = f"/unit/{self.UNIT_NUMBER}"
        link = (By.CSS_SELECTOR, f"a[href='{path}']")
        self.wait.until(EC.element_to_be_clickable(link)).click()
        self.wait.until(lambda driver: urlparse(driver.current_url).path == path)

    def open_key_ideas(self) -> None:
        self.wait.until(EC.element_to_be_clickable(self.KEY_IDEAS_TAB)).click()

    def _should_show_text(self, text: str) -> None:
        locator = (
            By.XPATH,
            f"//main//*[normalize-space()='{text}' "
            f"and not(.//*[normalize-space()='{text}'])]",
        )
        self.wait.until(
            EC.visibility_of_any_elements_located(locator),
            message=f"Unit {self.UNIT_NUMBER} should display {text!r}",
        )

    def should_show_overview(self) -> None:
        for text in (
            "Dashboard",
            f"Unit {self.UNIT_NUMBER}",
            self.TITLE,
            self.SUBTITLE,
        ):
            self._should_show_text(text)
        for tab in self.TABS:
            locator = (
                By.XPATH,
                f"//main//a[starts-with(@href, '#section-')][.//span[normalize-space()='{tab}']]",
            )
            self.wait.until(
                EC.visibility_of_element_located(locator),
                message=f"Unit {self.UNIT_NUMBER} navigation should display {tab!r}",
            )

    def should_show_key_ideas(self) -> None:
        for text in (
            "Core concepts of this unit",
            "What is this unit about?",
            self.INTRODUCTION,
            "Three Key Ideas",
        ):
            self._should_show_text(text)
        for title, definition in self.DEFINITIONS:
            card = (
                By.XPATH,
                f"//main//*[not(*) and normalize-space()='{title}']"
                f"/ancestor::div[.//*[normalize-space()='{definition}']][1]",
            )
            self.wait.until(
                EC.visibility_of_element_located(card),
                message=f"Key Ideas should display the {title} card",
            )
            self._should_show_text(definition)

    def should_have_progress(
        self, percentage: int, completed_sections: int, total_sections: int
    ) -> None:
        progress = (By.CSS_SELECTOR, "main a[href='/dashboard'] + div span")
        sections = (
            By.XPATH,
            "//main//p[contains(normalize-space(), 'sections complete')]",
        )
        done = (
            By.XPATH,
            "//main//*[@id='section-keyideas']//*[normalize-space()='Done']",
        )
        expected = (f"{percentage}%", f"{completed_sections} of {total_sections} sections complete", True)

        def actual_state() -> tuple[str, str, bool]:
            return (
                self.driver.find_element(*progress).text.strip(),
                self.driver.find_element(*sections).text.strip(),
                any(element.is_displayed() for element in self.driver.find_elements(*done)),
            )

        try:
            self.wait.until(lambda _: actual_state() == expected)
        except TimeoutException as error:
            raise AssertionError(
                f"Unit {self.UNIT_NUMBER} progress (percentage, sections, Key Ideas Done): "
                f"expected {expected!r}, got {actual_state()!r}"
            ) from error
