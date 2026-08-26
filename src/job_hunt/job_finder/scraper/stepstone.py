"""Scraper implementation for StepStone."""

from job_hunt.job_finder.scraper.base import BoardCSSSelectors

from .base import JobBoard


class StepstoneBoard(JobBoard):
    """Scraper class for the StepStone job search website."""

    _BOARD_CSS_SELECTORS = BoardCSSSelectors(
        job_results='[role="group"] > [data-testid="job-item"]',
        job_results_url="h2 a",
        job_results_title="h2 a",
        job_results_company='[data-at="job-item-company-name"]',
        next_page='[aria-label="Nächste"]',
        profile='[data-testid="menu-item-profile"]',
        job_desc_page_title='h1[data-at="header-job-title"]',
        job_desc_page_company='[data-at="metadata-company-name"]',
        job_desc_page_description='[data-at="job-ad-content"]',
        job_results_empty_banner="",  # doesn't support
    )

    def _signin(self) -> bool:
        """Sign in to StepStone if not already logged in."""
        if self._browser.is_visible(by_css=self._BOARD_CSS_SELECTORS.profile):
            return True

        self._browser.open("https://www.stepstone.de/de-DE/candidate/login")

        self._browser.wait_for_visible(by_id="app-header", timeout=10)

        self._accept_cookies()

        self._browser.wait_for_visible(by_id="app-header", timeout=10)

        if self._browser.is_visible(by_css=self._BOARD_CSS_SELECTORS.profile):
            return True

        return self.__signin_loop()

    def _accept_cookies(self) -> None:
        """Accept cookie consent dialog using stored preferences or clicking the button."""
        val = self._browser.execute_js("return window.localStorage.getItem('consent_level');")
        if val is None:
            css_cookie_accept = "[id='ccmgt_explicit_accept']"
            self._browser.click(by_css=css_cookie_accept)

    def __signin_loop(self) -> bool:
        """Perform input of credentials and wait for sign-in process to finish."""
        # sometimes it is failing
        if self._browser.is_visible(by_css=self._BOARD_CSS_SELECTORS.profile):
            return True

        self._browser.type(by_css='[data-testid="email-input"]', text=self._credentials.username)
        self._browser.type(by_css='[data-testid="password-input"]', text=self._credentials.password)
        self._browser.click(by_css='[data-testid="login-submit-btn"]')

        self._browser.wait_for_visible(by_css=self._BOARD_CSS_SELECTORS.profile, timeout=30)
        return True
