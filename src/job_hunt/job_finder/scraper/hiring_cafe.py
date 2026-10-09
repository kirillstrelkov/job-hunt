"""Scraper implementation for HiringCafe."""

from loguru import logger

from job_hunt.job_finder.scraper.base import BaseJob, BoardCSSSelectors

from .base import JobBoard


class HiringCafeBoard(JobBoard):
    """Scraper class for the HiringCafe job search website."""

    _BOARD_CSS_SELECTORS = BoardCSSSelectors(
        job_results=".hc-card-grid > div, .grid > div",
        job_results_url="a",
        job_results_title="span.w-full",
        job_results_company=".line-clamp-3 .font-bold",
        next_page='a[aria-label="Next page"]',
        profile="button .rounded-full .to-pink-500",
        job_desc_page_title=".flex h1",
        job_desc_page_company=".flex-1 div.font-bold",
        job_desc_page_description="article",
        job_results_empty_banner='div[aria-label="animation"]',
    )

    def _next_page(self) -> None:
        """Go to the next page and wait for the job cards to update."""
        if not self._browser.is_visible(by_css=self._BOARD_CSS_SELECTORS.next_page):
            return

        cur_url = self._browser.get_current_url()
        cards = self._browser.find_elements(by_css=self._BOARD_CSS_SELECTORS.job_results)
        old_card = cards[0] if cards else None

        self._browser.click(by_css=self._BOARD_CSS_SELECTORS.next_page)

        def _page_transitioned(_: object) -> bool:
            if old_card:
                try:
                    _ = old_card.tag_name
                    return False
                except Exception:
                    return True
            return cur_url != self._browser.get_current_url()

        try:
            self._browser.webdriver_wait(_page_transitioned, timeout=10)
        except Exception as e:
            logger.warning("failed to wait for page transition: {}", e)

        self._browser.wait_for_visible(by_css=self._BOARD_CSS_SELECTORS.job_results, timeout=10)

    def _get_base_jobs_from_current_page(self) -> list[BaseJob]:
        """Scrape job URLs from the current HiringCafe search results page."""
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

    def _get_base_jobs_from_all_pages(self, url: str | None = None, limit: int | None = None) -> list[BaseJob]:
        """Get unique base jobs from all pages starting with supplied url and going through all pages."""
        if url:
            self.open(url)

        base_jobs: list[BaseJob] = []
        for job in self._get_base_jobs_from_current_page():
            if job not in base_jobs:
                base_jobs.append(job)

        logger.debug("Found {} jobs", len(base_jobs))

        while self._has_next_page():
            if limit and len(base_jobs) >= limit:
                break

            logger.debug("Going to the next page")

            self._next_page()
            new_links = self._get_base_jobs_from_current_page()

            logger.debug("Found {} jobs", len(new_links))

            for job in new_links:
                if job not in base_jobs:
                    base_jobs.append(job)

        base_jobs = base_jobs[:limit] if limit else base_jobs

        logger.info("Found total {} jobs", len(base_jobs))

        unique_jobs = self._filter_base_jobs(base_jobs)

        logger.info("Found unique {} jobs", len(unique_jobs))

        return unique_jobs

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
