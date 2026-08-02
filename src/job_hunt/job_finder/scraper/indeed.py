"""Scraper implementation for Indeed."""

from job_hunt.job_finder.scraper.base import BoardCSSSelectors

from .base import JobBoard


class IndeedBoard(JobBoard):
    """Scraper class for the Indeed job search website."""

    _BOARD_CSS_SELECTORS = BoardCSSSelectors(
        job_results='div:not([class*="recommendation-section"]).result .mainContentTable .resultContent',
        job_results_url="a",
        job_results_company='[data-testid="company-name"]',
        next_page='a[data-testid="pagination-page-next"]',
        profile='button[id="AccountMenu"]',
        job_desc_page_title='[data-testid="jobsearch-JobInfoHeader-title"]',
        job_desc_page_company='[data-testid="inlineHeader-companyName"]',
        job_desc_page_description='[id="jobDescriptionText"]',
        job_results_empty_banner=".jobsearch-NoResult-messageContainer",
    )

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
