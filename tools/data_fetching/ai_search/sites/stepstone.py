import os

from base import Page
from linkedin import Job
from loguru import logger


class StepstonePage(Page):
    def _signin(self) -> bool:
        css_profile = '[data-testid="menu-item-profile"]'
        if self._browser.is_visible(by_css=css_profile):
            return True

        self._browser.open("https://www.stepstone.de/de-DE/candidate/login")

        self._browser.wait_for_visible(by_tag="body", timeout=10)

        self._accept_cookies()

        if self._browser.is_visible(by_css=css_profile):
            return True

        return self.__signin_loop()

    def _accept_cookies(self) -> None:
        val = self._browser.execute_js("return window.localStorage.getItem('consent_level');")
        if val is None:
            css_cookie_accept = "[id='ccmgt_explicit_accept']"
            self._browser.click(by_css=css_cookie_accept)

    def __signin_loop(self) -> bool:
        self._browser.type(by_css='[data-testid="email-input"]', text=self._credentials.username)
        self._browser.type(by_css='[data-testid="password-input"]', text=self._credentials.password)
        self._browser.click(by_css='[data-testid="login-submit-btn"]')

        css_profile = '[data-testid="menu-item-profile"]'
        self._browser.wait_for_visible(by_css=css_profile, timeout=30)
        return True

    def _get_job(self, url: str | None = None) -> Job:
        if url:
            self.open(url)

        desc = self._browser.get_text(by_css='[data-at="job-ad-content"]')
        url = self._browser.get_current_url()
        url = url.split("?")[0]
        title = self._browser.get_text(by_css='h1[data-at="header-job-title"]').strip()
        company = self._browser.get_text(by_css='[data-at="metadata-company-name"]').strip()
        return Job(title=title, company=company, url=url, description=desc, error="")

    def _get_job_urls(self) -> list[str]:
        css_job_links = '[role="group"] > [data-testid="job-item"] h2 a'
        job_links = self._browser.find_elements(by_css=css_job_links)
        return [self._browser.get_attribute(job, "href") for job in job_links]

    def _next_page(self) -> None:
        css_next_page = '[aria-label="Nächste"]'
        if self._browser.is_visible(by_css=css_next_page):

            def _click(_) -> bool | None:
                try:
                    self._browser.click(by_css=css_next_page)
                    return True
                except:
                    return not self._browser.is_visible(by_css=css_next_page)

            try:
                self._browser.webdriver_wait(_click, timeout=10)
            except Exception as e:
                logger.warning("failed to get next page: {}", e)

    def _has_next_page(self) -> bool:
        css_next_page = '[aria-label="Nächste"]'
        self._browser.wait_for_present(by_css=css_next_page)
        return not bool(self._browser.get_attribute(by_css=css_next_page, attr="disabled"))
