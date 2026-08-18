"""Scraper implementation for HiringCafe."""

from job_hunt.job_finder.scraper.base import BoardCSSSelectors

from .base import JobBoard


class HiringCafeBoard(JobBoard):
    """Scraper class for the HiringCafe job search website."""

    _BOARD_CSS_SELECTORS = BoardCSSSelectors(
        job_results=".grid > div",
        job_results_url="a",
        job_results_company=".font-light .font-bold",
        next_page='a[aria-label="Next page"]',
        profile="button .rounded-full .to-pink-500",
        job_desc_page_title=".flex h1",
        job_desc_page_company=".flex-1 div.font-bold",
        job_desc_page_description="article",
        job_results_empty_banner='div[aria-label="animation"]',
    )

    def _signin(self) -> bool:
        """Sign in to HiringCafe if not already logged in."""
        if self._is_logged_in():
            return True

        self._browser.open("https://hiringcafe.com/auth")

        self._browser.wait_for_visible(by_tag="body", timeout=10)

        if self._is_logged_in():
            return True

        return self.__signin_loop()

    def __signin_loop(self) -> bool:
        """Perform the login credentials input and wait for login completion."""
        css_email = 'input[type="email"]'
        if not self._browser.is_visible(by_css=css_email):
            return True

        self._browser.type(by_css=css_email, text=self._credentials.username)
        self._browser.type(by_css='input[type="password"]', text=self._credentials.password + "\n")

        self._browser.wait_for_visible(by_css=self._BOARD_CSS_SELECTORS.profile, timeout=self._SINGIN_TIMEOUT)
        return True
