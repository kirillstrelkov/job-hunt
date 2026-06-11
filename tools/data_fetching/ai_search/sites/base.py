import atexit
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Generator
from traceback import format_exc

from easelenium.browser import Browser
from loguru import logger
from selenium.common.exceptions import WebDriverException
from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt

from caching_utils import get_cached_value, get_hashsum, has_cached_value
from common_utils import get_browser as _get_browser
from job.ai_search.env_utils import get_credentials

__BROWSER = None


def get_browser() -> Browser:
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
    _instance = None

    def __new__(cls, *args, **kwargs) -> "_SingleBrowser":
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
    title: str
    company: str
    url: str
    description: str
    error: str


def make_job(title: str = "", company: str = "", url: str = "", description: str = "", error: str = "") -> Job:
    return Job(title=title, company=company, url=url, description=description, error=error)


class Page:
    # timeout should be long enough to verify login via phone app or via email or validate capcha
    _SINGIN_TIMEOUT = 60

    # css used by default implementations - should be overriden in sub classes or method should be overriden
    _CSS_NEXT_PAGE = None
    _CSS_PROFILE = None

    def __init__(self, browser: Browser, *, use_cache: bool = False) -> None:
        """Create a Page object."""
        self._browser = browser
        self._use_cache = use_cache
        self._credentials = get_credentials(self.__class__.__name__.removesuffix("Page"))

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
        assert self._CSS_NEXT_PAGE

        if self._browser.is_visible(by_css=self._CSS_NEXT_PAGE):

            def _click(_) -> bool | None:
                cur_url = self._browser.get_current_url()
                try:
                    self._browser.click(by_css=self._CSS_NEXT_PAGE)
                    return cur_url != self._browser.get_current_url()
                except:
                    return not self._browser.is_visible(by_css=self._CSS_NEXT_PAGE)

            try:
                self._browser.webdriver_wait(_click, timeout=10)
            except Exception as e:
                logger.warning("failed to get next page: {}", e)

    def _has_next_page(self) -> bool:
        """Check if there is a next page."""
        assert self._CSS_NEXT_PAGE

        return self._browser.is_visible(by_css=self._CSS_NEXT_PAGE)

    def _is_logged_in(self) -> bool:
        """Check if there is a next page."""
        assert self._CSS_PROFILE

        return self._browser.is_visible(by_css=self._CSS_PROFILE)

    # should be implemented:

    def _signin(self) -> bool:
        raise NotImplementedError

    def _get_job_urls(self) -> list[str]:
        """Get job URLs from the page."""
        raise NotImplementedError

    def _get_job(self, url: str | None = None) -> Job:
        """Get job from the current page."""
        raise NotImplementedError

    # methods with caching

    def get_job(self, url: str | None = None) -> Job:
        """Get job from the current page."""
        url = url or self._browser.get_current_url()

        # TODO: do we need retries?
        # @retry(
        #     retry=retry_if_exception_type(WebDriverException),
        #     stop=stop_after_attempt(3),
        # )
        def get_job_with_retry() -> Job:
            return self._get_job(url)

        def wrap_get_job() -> Job:
            try:
                return get_job_with_retry()
            except Exception:
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
