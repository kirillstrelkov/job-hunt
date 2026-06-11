
from .base import Page
from .linkedin import Job


class IndeedPage(Page):
    _CSS_PROFILE = 'button[id="AccountMenu"]'
    _CSS_NEXT_PAGE = 'a[data-testid="pagination-page-next"]'

    def _signin(self) -> bool:
        if self._is_logged_in():
            return True

        self._browser.open("https://secure.indeed.com/auth")

        self._browser.wait_for_visible(by_tag="body", timeout=10)

        self._accept_cookies()

        if self._is_logged_in():
            return True

        return self.__signin_loop()

    def _accept_cookies(self) -> None:
        css_cookie_accept = '[id="onetrust-accept-btn-handler"]'
        if self._browser.is_visible(by_css=css_cookie_accept):
            self._browser.click(by_css=css_cookie_accept)

    def __signin_loop(self) -> bool:
        self._browser.type(by_css='input[type="email"]', text=self._credentials.username + "\n")

        self._browser.wait_for_visible(by_css=self._CSS_PROFILE, timeout=self._SINGIN_TIMEOUT)
        return True

    def _get_job(self, url: str | None = None) -> Job:
        if url:
            self.open(url)

        desc = self._browser.get_text(by_id="jobDescriptionText")
        url = self._browser.get_current_url()
        title = self._browser.get_text(by_css='[data-testid="jobsearch-JobInfoHeader-title"]').strip()
        company = self._browser.get_text(by_css='[data-testid="inlineHeader-companyName"]').strip()
        return Job(title=title, company=company, url=url, description=desc, error="")

    def _get_job_urls(self) -> list[str]:
        css_job_links = 'div:not([class*="recommendation-section"]).result .mainContentTable a'
        job_links = self._browser.find_elements(by_css=css_job_links)
        return [self._browser.get_attribute(job, "href") for job in job_links if self._browser.is_visible(job)]
