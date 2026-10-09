"""Scraper implementation for Indeed."""

from time import sleep

from loguru import logger
from selenium.webdriver.common.action_chains import ActionChains

from job_hunt.job_finder.scraper.base import BaseJob, BoardCSSSelectors

from .base import JobBoard


class IndeedBoard(JobBoard):
    """Scraper class for the Indeed job search website."""

    _BOARD_CSS_SELECTORS = BoardCSSSelectors(
        job_results='div:not([class*="recommendation-section"]).result .mainContentTable .resultContent',
        job_results_url="a",
        job_results_title="a",
        job_results_company='[data-testid="company-name"]',
        next_page='a[data-testid="pagination-page-next"]',
        profile='button[id="AccountMenu"]',
        job_desc_page_title='[data-testid="vj-job-title"], [data-testid="jobsearch-JobInfoHeader-title"]',
        job_desc_page_company='[data-testid="inlineHeader-companyName"], [data-testid="company-info-metadata"] a, [data-testid="company-info-metadata"] > div > div:first-child',
        job_desc_page_description='.simple-job-description-html, [id="jobDescriptionText"]',
        job_results_empty_banner=".jobsearch-NoResult-messageContainer",
    )

    def open(self, url: str) -> None:
        """Open the page with the given URL and handle Cloudflare challenge if present."""
        super().open(url)
        self._handle_cloudflare()

    def _next_page(self) -> None:
        """Navigate to next page and handle Cloudflare challenge if present."""
        super()._next_page()
        self._handle_cloudflare()

    def _handle_cloudflare(self) -> None:
        """Detect and solve Cloudflare Turnstile challenge if present."""
        for _ in range(5):
            if "Just a moment" not in self._browser.get_title():
                return
            logger.info("Cloudflare Turnstile detected on Indeed, attempting bypass...")
            box_coords = self._browser._driver.execute_script("""
                let el = document.getElementById('cf-box-container');
                if (!el) return null;
                let target = el.querySelector('#DEYIo7') || el.querySelector('.main-content > div') || el;
                let rect = target.getBoundingClientRect();
                return {x: rect.left, y: rect.top, width: rect.width, height: rect.height};
            """)
            if box_coords and box_coords.get("width", 0) > 0:
                click_x = int(box_coords["x"] + 30)
                click_y = int(box_coords["y"] + box_coords["height"] / 2)
                actions = ActionChains(self._browser._driver)
                try:
                    actions.w3c_actions.pointer_action.move_to_location(click_x, click_y)
                    actions.w3c_actions.pointer_action.click()
                    actions.perform()
                except Exception:
                    ActionChains(self._browser._driver).move_by_offset(click_x, click_y).click().perform()
            for _ in range(5):
                sleep(1)
                if "Just a moment" not in self._browser.get_title():
                    logger.info("Cloudflare Turnstile challenge solved.")
                    return

    def _get_base_jobs_from_current_page(self) -> list[BaseJob]:
        """Scrape job URLs from the current Indeed search results page."""
        css_results = self._BOARD_CSS_SELECTORS.job_results
        css_empty = self._BOARD_CSS_SELECTORS.job_results_empty_banner

        def _is_empty_banner_visible() -> bool:
            return bool(css_empty and self._browser.is_visible(by_css=css_empty))

        if _is_empty_banner_visible():
            return []

        combined_selector = f"{css_results}, {css_empty}" if css_empty else css_results
        try:
            self._browser.wait_for_visible(by_css=combined_selector, timeout=10)
        except Exception:
            if _is_empty_banner_visible() or not self._browser.is_visible(by_css=css_results):
                return []
            raise

        if _is_empty_banner_visible():
            return []

        job_results = self._browser.find_elements(by_css=css_results)
        jobs = [self._get_single_base_job_from_search_results(job_result) for job_result in job_results]
        return [j for j in jobs if j.url and j.title]

    def _signin(self) -> bool:
        """Sign in to Indeed if not already logged in."""
        if self._is_logged_in():
            return True

        self._browser.open("https://secure.indeed.com/auth")

        self._browser.wait_for_visible(by_tag="body", timeout=10)

        self._accept_cookies()

        if self._is_logged_in():
            return True

        return self.__signin_loop()

    def _accept_cookies(self) -> None:
        """Accept cookie consent dialog if present."""
        css_cookie_accept = '[id="onetrust-accept-btn-handler"]'
        if self._browser.is_visible(by_css=css_cookie_accept):
            self._browser.click(by_css=css_cookie_accept)

    def __signin_loop(self) -> bool:
        """Perform the login credentials input and wait for login completion."""
        css_email = 'input[type="email"]'
        self._browser.wait_for_visible(by_css=css_email)
        self._browser.type(by_css=css_email, text=self._credentials.username + "\n")

        self._browser.wait_for_visible(by_css=self._BOARD_CSS_SELECTORS.profile, timeout=self._SINGIN_TIMEOUT)
        return True
