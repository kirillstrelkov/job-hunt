"""Base scraper module defining shared classes and utilities."""

import atexit
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from traceback import format_exc
from typing import Self

from easelenium.browser import Browser
from loguru import logger
from selenium.common.exceptions import WebDriverException
from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt

from job_finder.utils.caching_utils import get_cached_value, get_hashsum, has_cached_value
from job_finder.utils.common_utils import get_browser as _get_browser
from job_finder.utils.env_utils import get_credentials

__BROWSER = None


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


@dataclass(frozen=True)
class Job:
    """Represents a job description model."""

    title: str
    company: str
    url: str = field(compare=False)
    description: str
    error: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC), compare=False)


def make_job(
    *,
    title: str = "",
    company: str = "",
    url: str = "",
    description: str = "",
    error: str = "",
    created_at: datetime | None = None,
) -> Job:
    """Create a Job instance."""
    kwargs = {
        "title": title,
        "company": company,
        "url": url,
        "description": description,
        "error": error,
    }
    if created_at is not None:
        kwargs["created_at"] = created_at
    return Job(**kwargs)


class JobBoard:
    """Base class for scrapers of different job sites."""

    # timeout should be long enough to verify login via phone app or via email or validate capcha
    _SINGIN_TIMEOUT = 60

    # css used by default implementations - should be overriden in sub classes or method should be overriden
    _CSS_NEXT_PAGE = None
    _CSS_PROFILE = None

    def __init__(self, browser: Browser, *, use_cache: bool = False) -> None:
        """Create a JobBoard object."""
        self._browser = browser
        self._use_cache = use_cache
        self._credentials = get_credentials(self.__class__.__name__.removesuffix("Board"))

        logger.info("Signing in...")
        self._signin()
        logger.info("Signed in.")

    def _get_job_links(self, url: str | None = None, limit: None | int = None) -> list[str]:
        """Get jobs from the current page."""
        if url:
            self.open(url)

        job_links = self.get_job_urls()

        logger.debug("Found {} jobs", len(job_links))

        while self._has_next_page():
            if limit and len(job_links) >= limit:
                break

            logger.debug("Going to the next page")

            self._next_page()
            new_links = self.get_job_urls()

            logger.debug("Found {} jobs", len(new_links))

            job_links += new_links

        job_links = job_links[:limit] if limit else job_links

        logger.info("Found total {} jobs", len(job_links))

        return job_links

    def get_jobs(self, url: str | None = None, limit: None | int = None) -> list[Job]:
        """Get jobs from the current page."""
        job_links = self._get_job_links(
            url,
            limit,
        )

        jobs = []
        for job_url in job_links:
            try:
                job = self.get_job(job_url)
                jobs.append(job)
            except RetryError as e:
                logger.warning(f"failed to get {job_url}: {e}")

        return jobs

    def open(self, url: str) -> None:
        """Open the page with the given URL."""
        logger.info("Opening {}", url)
        self._browser.get(url)

    # implemented by default:

    def _next_page(self) -> None:
        """Go to the next page."""
        if not self._CSS_NEXT_PAGE:
            msg = "CSS_NEXT_PAGE must be defined"
            raise ValueError(msg)

        if self._browser.is_visible(by_css=self._CSS_NEXT_PAGE):

            def _click(_: object) -> bool | None:
                cur_url = self._browser.get_current_url()
                try:
                    self._browser.click(by_css=self._CSS_NEXT_PAGE)
                    return cur_url != self._browser.get_current_url()
                except Exception:  # noqa: BLE001
                    return not self._browser.is_visible(by_css=self._CSS_NEXT_PAGE)

            try:
                self._browser.webdriver_wait(_click, timeout=10)
            except Exception as e:  # noqa: BLE001
                logger.warning("failed to get next page: {}", e)

    def _has_next_page(self) -> bool:
        """Check if there is a next page."""
        if not self._CSS_NEXT_PAGE:
            msg = "CSS_NEXT_PAGE must be defined"
            raise ValueError(msg)

        return self._browser.is_visible(by_css=self._CSS_NEXT_PAGE)

    def _is_logged_in(self) -> bool:
        """Check if there is a next page."""
        if not self._CSS_PROFILE:
            msg = "CSS_PROFILE must be defined"
            raise ValueError(msg)

        return self._browser.is_visible(by_css=self._CSS_PROFILE)

    # should be implemented:

    def _signin(self) -> bool:
        """Sign in to the website. Should be implemented by subclasses."""
        raise NotImplementedError

    def _get_job_urls(self) -> list[str]:
        """Get job URLs from the page."""
        raise NotImplementedError

    def _get_job(self, url: str | None = None) -> Job:
        """Get job from the current page."""
        raise NotImplementedError

    # methods with caching

    # Future: fix on error - add retry 3 times if failed - just return with error?
    def get_job(self, url: str | None = None) -> Job:
        """Get job from the current page."""
        url = url or self._browser.get_current_url()

        def get_job_with_retry() -> Job:
            return self._get_job(url)

        def wrap_get_job() -> Job:
            try:
                return get_job_with_retry()
            except Exception:  # noqa: BLE001
                e_stack = format_exc()
                logger.error("creating default job due to exception: {}", e_stack)
                return make_job(url=url, error=e_stack)

        if not self._use_cache:
            return wrap_get_job()

        args = "job_obj", url
        hs = get_hashsum(*args)
        if has_cached_value(hs):
            logger.debug("Using hashed value for {}", args)
        return get_cached_value(hs, wrap_get_job)

    @retry(
        retry=retry_if_exception_type(WebDriverException),
        stop=stop_after_attempt(3),
    )
    def get_job_urls(self) -> list[str]:
        """Get job from the current page."""
        url = self._browser.get_current_url()

        if not self._use_cache:
            return self._get_job_urls()

        args = "job_urls", url
        hs = get_hashsum(*args)
        if has_cached_value(hs):
            logger.debug("Using hashed value for {}", args)

        return get_cached_value(hs, self._get_job_urls)
