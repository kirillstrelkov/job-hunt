"""Base scraper module defining shared classes and utilities."""

import atexit
from collections import defaultdict
from collections.abc import Callable, Generator
from contextlib import contextmanager
from traceback import format_exc
from typing import Self

from easelenium.browser import Browser
from loguru import logger
from pydantic import BaseModel
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt

from job_hunt.job_finder.utils.caching_utils import get_cached_value, get_hashsum, has_cached_value
from job_hunt.job_finder.utils.common_utils import get_browser as _get_browser
from job_hunt.job_finder.utils.env_utils import get_credentials
from job_hunt.job_finder.utils.models import BaseJob, Job, make_job

__BROWSER = None


def _get_safely_object_or_none(func: Callable[[], object]) -> object | None:
    try:
        return func()
    except Exception as e:
        logger.warning("Exception: {}", e)
        return None


def get_browser() -> Browser:
    """Get the singleton browser instance."""
    return _SingleBrowser().browser


@contextmanager
def browser_context() -> Generator[Browser]:
    """Context manager for Browser."""
    browser = _get_browser(show_images=True)

    try:
        yield browser
    finally:
        browser.quit()


class _SingleBrowser:
    """Singleton helper class to manage a single browser instance."""

    _instance = None

    def __new__(cls, *_args: object, **_kwargs: object) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.browser = _get_browser(show_images=True)

            atexit.register(cls._cleanup)

        return cls._instance

    @classmethod
    def _cleanup(cls) -> None:
        if cls._instance and cls._instance.browser:
            cls._instance.browser.quit()


class BoardCSSSelectors(BaseModel):
    """CSS selectors for job boards."""

    job_results: str
    job_results_url: str
    job_results_company: str
    next_page: str
    profile: str
    job_desc_page_title: str
    job_desc_page_company: str
    job_desc_page_description: str
    job_results_empty_banner: str


class JobBoard:
    """Base class for scrapers of different job sites."""

    # timeout should be long enough to verify login via phone app or via email or validate capcha
    _SINGIN_TIMEOUT = 60

    # css used by default implementations - should be overriden in sub classes or method should be overriden
    _BOARD_CSS_SELECTORS: BoardCSSSelectors

    def __init__(
        self,
        browser: Browser,
        *,
        use_cache: bool = False,
        excluded_companies: list[str] | None = None,
        excluded_title_keywords: list[str] | None = None,
    ) -> None:
        """Create a JobBoard object."""
        assert self._BOARD_CSS_SELECTORS

        self._browser = browser
        self._use_cache = use_cache
        self._credentials = get_credentials(self.__class__.__name__.removesuffix("Board"))
        self._excluded_companies = excluded_companies or []
        self._excluded_title_keywords = excluded_title_keywords or []

        logger.info("Signing in...")
        self._signin()
        logger.info("Signed in.")

    def open(self, url: str) -> None:
        """Open the page with the given URL."""
        logger.info("Opening {}", url)
        self._browser.get(url)

    # method with caching
    @retry(
        retry=retry_if_exception_type(WebDriverException),
        stop=stop_after_attempt(3),
    )
    def get_all_jobs(self, url: str | None = None, limit: int | None = None) -> list[Job]:
        """Get all jobs from all pages.

        This method uses caching and retry logic on WebDriverException.

        """
        url = url or self._browser.get_current_url()

        if not self._use_cache:
            return self._get_all_jobs_from_all_pages(url, limit)

        args = "jobs", url
        hs = get_hashsum(*args)
        if has_cached_value(hs):
            logger.debug("Using hashed value for {}", args)

        return get_cached_value(hs, lambda: self._get_all_jobs_from_all_pages(url, limit))

    # implemented by default:
    def _get_all_jobs_from_all_pages(self, url: str | None = None, limit: int | None = None) -> list[Job]:
        """Get all jobs from all pages."""
        base_jobs = self._get_base_jobs_from_all_pages(url, limit)

        jobs = []
        for base_job in base_jobs:
            try:
                job = self._convert_base_job_to_job_by_getting_description(base_job)
                jobs.append(job)
            except RetryError as e:
                logger.warning(f"failed to get {base_job}: {e}")

        return jobs

    # Future: fix on error - add retry 3 times if failed - just return with error?
    # method with caching
    def _convert_base_job_to_job_by_getting_description(self, base_job: BaseJob) -> Job:
        """Convert base job to job with subclassed _get_job_with_description method.

        This method uses caching and retry logic on WebDriverException.
        """

        def wrap_get_job() -> Job:
            try:
                return self._get_job_with_description(job=base_job)
            except Exception:
                e_stack = format_exc()
                logger.error("creating default job due to exception: {}", e_stack)
                return make_job(base_job=base_job, error=e_stack)

        if not self._use_cache:
            return wrap_get_job()

        args = "job", base_job.url
        hs = get_hashsum(*args)
        if has_cached_value(hs):
            logger.debug("Using hashed value for {}", args)
        return get_cached_value(hs, wrap_get_job)

    def _filter_base_jobs(self, jobs: list[BaseJob]) -> list[BaseJob]:
        """Filter jobs by excluded companies and title keywords."""
        filtered_jobs: list[BaseJob] = []

        excluded_jobs = defaultdict(list)

        for job in jobs:
            is_excluded = False
            for company in self._excluded_companies:
                if company in job.company.lower():
                    excluded_jobs[company].append(job)
                    is_excluded = True
                    break

            if is_excluded:
                continue

            for keyword in self._excluded_title_keywords:
                if keyword in job.title.lower():
                    excluded_jobs[keyword].append(job)
                    is_excluded = True
                    break

            if not is_excluded:
                filtered_jobs.append(job)

        for trigger, ex_jobs in excluded_jobs.items():
            logger.warning("Jobs {} excluded due to {}", len(ex_jobs), trigger)

        return filtered_jobs

    def _get_base_jobs_from_all_pages(self, url: str | None = None, limit: int | None = None) -> list[BaseJob]:
        """Get base jobs from all pages starting with supplied url and going through all pages."""
        if url:
            self.open(url)

        base_jobs = self._get_base_jobs_from_current_page()

        logger.debug("Found {} jobs", len(base_jobs))

        while self._has_next_page():
            if limit and len(base_jobs) >= limit:
                break

            logger.debug("Going to the next page")

            self._next_page()
            new_links = self._get_base_jobs_from_current_page()

            logger.debug("Found {} jobs", len(new_links))

            base_jobs += new_links

        base_jobs = base_jobs[:limit] if limit else base_jobs

        logger.info("Found total {} jobs", len(base_jobs))

        unique_jobs = self._filter_base_jobs(base_jobs)

        logger.info("Found unique {} jobs", len(unique_jobs))

        return unique_jobs

    def _next_page(self) -> None:
        """Go to the next page."""
        if self._browser.is_visible(by_css=self._BOARD_CSS_SELECTORS.next_page):

            def _click(_: object) -> bool | None:
                cur_url = self._browser.get_current_url()
                try:
                    self._browser.click(by_css=self._BOARD_CSS_SELECTORS.next_page)
                    return cur_url != self._browser.get_current_url()
                except Exception:
                    return not self._browser.is_visible(by_css=self._BOARD_CSS_SELECTORS.next_page)

            try:
                self._browser.webdriver_wait(_click, timeout=10)
            except Exception as e:
                logger.warning("failed to get next page: {}", e)

    def _has_next_page(self) -> bool:
        """Check if there is a next page."""
        return (
            self._browser.is_visible(by_css=self._BOARD_CSS_SELECTORS.next_page)
            and self._browser.find_element(by_css=self._BOARD_CSS_SELECTORS.next_page).is_enabled()
        )

    def _is_logged_in(self) -> bool:
        """Check if there is a next page."""
        if not self._BOARD_CSS_SELECTORS.profile:
            msg = "CSS_PROFILE must be defined"
            raise ValueError(msg)

        return self._browser.is_visible(by_css=self._BOARD_CSS_SELECTORS.profile)

    def _get_single_base_job_from_search_results(self, element: WebElement) -> BaseJob:
        url = _get_safely_object_or_none(
            lambda: self._browser.get_attribute(
                parent=element,
                by_css=self._BOARD_CSS_SELECTORS.job_results_url,
                visible=False,
                attr="href",
            )
        )
        title = _get_safely_object_or_none(
            lambda: self._browser.get_text(
                parent=element,
                by_css=self._BOARD_CSS_SELECTORS.job_results_url,
                visible=False,
            ).strip()
        )
        company = _get_safely_object_or_none(
            lambda: self._browser.get_text(
                parent=element,
                by_css=self._BOARD_CSS_SELECTORS.job_results_company,
                visible=False,
            ).strip()
        )

        error = f"Failed to parse: {url=}, {title=}, {company=}" if None in [url, title, company] else ""

        return BaseJob(
            url=url or "",
            title=title or "",
            company=company or "",
            error=error,
        )

    # might be overridden if default implementation doesn't work

    def _get_base_jobs_from_current_page(self) -> list[BaseJob]:
        """Scrape job URLs from the current StepStone search results page."""

        def _is_no_jobs() -> bool:
            return bool(
                self._BOARD_CSS_SELECTORS.job_results_empty_banner
                and self._browser.is_visible(by_css=self._BOARD_CSS_SELECTORS.job_results_empty_banner)
            )

        if _is_no_jobs():
            return []

        self._browser.wait_for_visible(by_css=self._BOARD_CSS_SELECTORS.job_results)
        job_results = self._browser.find_elements(by_css=self._BOARD_CSS_SELECTORS.job_results)

        # second time if not found banner loaded dynamically
        if _is_no_jobs():
            return []

        return [self._get_single_base_job_from_search_results(job_result) for job_result in job_results]

    def _get_job_with_description(self, *, job: BaseJob | None = None, url: str | None = None) -> Job:
        """Extract job details (title, company, description) from job url."""
        if not ((job and not url) or (url and not job)):
            msg = "Either job or url must be provided"
            raise ValueError(msg)

        if url:
            job = BaseJob(url=url, title="", company="")

        self.open(job.url)
        title = job.title or self._browser.get_text(by_css=self._BOARD_CSS_SELECTORS.job_desc_page_title).strip()
        company = job.company or self._browser.get_text(by_css=self._BOARD_CSS_SELECTORS.job_desc_page_company).strip()

        desc = self._get_description_from_current_page()
        url = self._browser.get_current_url()  # override url if there are redirects

        return make_job(
            title=title,
            company=company,
            description=desc,
            url=url,
            base_job=job,
        )

    # some boards might override this method as description is dynamic
    def _get_description_from_current_page(self) -> str:
        """Get description from the current page."""
        return self._browser.get_text(by_css=self._BOARD_CSS_SELECTORS.job_desc_page_description)

    # should be implemented:

    def _signin(self) -> bool:
        """Sign in to the website. Should be implemented by subclasses."""
        raise NotImplementedError
