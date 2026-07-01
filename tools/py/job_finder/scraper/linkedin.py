"""Scraper implementation for LinkedIn."""

from collections.abc import Callable
from random import random
from time import sleep

from easelenium.browser import Browser
from loguru import logger
from selenium.webdriver.remote.webelement import WebElement

from .base import Job, JobBoard

_LINKEDIN_JOB_URL_TEMPLATE = "https://www.linkedin.com/jobs/view/{}"


def _find_first_visible(browser: Browser, **kwargs: object) -> WebElement:
    """Find and return the first visible element matching the criteria.

    If no elements are visible, wait for visibility and return the element.
    """
    _ = kwargs.pop("times", 0)

    for e in browser.find_elements(**kwargs):
        if browser.is_visible(element=e):
            return e

    browser.wait_for_visible(**kwargs, timeout=1)
    return browser.find_element(**kwargs)


class LinkedinBoard(JobBoard):
    """Scraper class for the LinkedIn job search website."""

    _CSS_NEXT_PAGE = '[aria-label="View next page"]'

    def _signin(self) -> bool:
        """Sign in to LinkedIn if not already logged in."""
        if self.__already_logged_in():
            return True

        self.open("https://www.linkedin.com/login")
        self._browser.wait_for_visible(by_css="body")

        self.__skip_welcome_back()

        if self.__already_logged_in():
            return True

        self._browser.type(
            _find_first_visible(self._browser, by_xpath='//input[@type="email"]'),
            text=self._credentials.username,
        )
        self._browser.type(
            _find_first_visible(self._browser, by_xpath='//input[@type="password"]'),
            text=self._credentials.password + "\n",
        )
        self.__wait_for_logged_in()

        sleep(random() * 3)  # noqa: S311

        return self.__already_logged_in()

    def __skip_welcome_back(self) -> None:
        """Skip the welcome back banner / member profile block if shown."""
        css_login_again = "#rememberme-div .member-profile-block"
        if self._browser.is_visible(by_css=css_login_again):
            self._browser.click(by_css=css_login_again)

    def __wait_for_logged_in(self) -> None:
        """Wait until the user is successfully logged in."""
        logger.debug("Waiting for logged in...")
        self._browser.webdriver_wait(lambda _: self.__already_logged_in(), timeout=self._SINGIN_TIMEOUT)

        logger.debug("Waiting for checkpoint is closed...")
        # long wait to manually pass security check
        self._browser.webdriver_wait(
            lambda _: "checkpoint" not in self._browser.get_current_url(), timeout=self._SINGIN_TIMEOUT
        )

    def __already_logged_in(self) -> bool:
        """Check if the user is already logged in to LinkedIn."""
        css_header_span_text = "header button>span>span"

        is_logged = any(
            ("Me" in e.text.strip() or "Sie" in e.text.strip())
            for e in self._browser.find_elements(by_css=css_header_span_text)
        )

        logger.debug(f"Loggedin {is_logged}")
        return is_logged

    def _get_job(self, url: str | None = None) -> Job:
        """Scrape job details from a LinkedIn job page."""
        if url:
            self.open(url)
        css_job_desc = "[componentkey*='AboutTheJob']"
        self._browser.wait_for_visible(by_css=css_job_desc)

        url = self._browser.get_current_url()

        # wait until text is fully loaded
        self._browser.webdriver_wait(
            lambda _: len(self._browser.get_attribute(by_css=css_job_desc, attr="textContent")) > 0,
            timeout=10,
        )

        text = self._browser.get_attribute(by_css=css_job_desc, attr="textContent").strip()

        company = self._browser.get_text(by_css="div > p > a").strip()
        title = self._browser.get_text(by_css="div[data-display-contents] > p").strip()

        logger.debug(
            "Got job: title '{}', company '{}', description[{}]: '{}...'",
            title,
            company,
            len(text),
            text[:20],
        )

        return Job(title=title, company=company, url=url, description=text, error="")

    def _get_job_urls(self) -> list[str]:
        """Scrape job URLs from the current LinkedIn job search list."""
        css_no_jobs = ".jobs-search-no-results-banner"
        if self._browser.is_visible(by_css=css_no_jobs):
            return []

        css_job_list_item = ".scaffold-layout__list  ul > li.ember-view"

        def find_jobs() -> list[WebElement]:
            return self._browser.find_elements(by_css=css_job_list_item)

        self.__wait_for_same_result(lambda: len(find_jobs()))

        # additional just to be sure banner is not shown after wait
        if self._browser.is_visible(by_css=css_no_jobs):
            return []

        return [
            _LINKEDIN_JOB_URL_TEMPLATE.format(self._browser.get_attribute(element=e, attr="data-occludable-job-id"))
            for e in find_jobs()
        ]

    def __wait_for_same_result(self, func: Callable[[], int], times: int = 5) -> None:
        """Wait for same result of func to appears number of times."""
        # special wait as jobs are loaded dynamically - wait until 5 times is same result
        holder = {
            "times": times,
            "prev_result": func(),
        }

        def _is_same_result(_driver: object) -> bool:
            if holder["times"] == 0:
                return True

            result_cur = func()
            if holder["prev_result"] == result_cur:
                holder["times"] -= 1
                sleep(0.03)
            else:
                holder["times"] = times
                holder["prev_result"] = result_cur

            return False

        self._browser.webdriver_wait(_is_same_result, timeout=40)
