"""Common utility functions for numbers and browser decorators."""

import os
import re
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from tempfile import gettempdir
from typing import Any

from easelenium.browser import Browser


def get_number(text: object) -> int:
    """Extract the first number found in the text as an integer.

    Args:
        text: The source object/text to search for numbers.

    Returns:
        The first integer found.

    """
    return get_numbers(text)[0]


def get_numbers(text: object) -> list[int]:
    """Extract all numbers found in the text as a list of integers.

    Args:
        text: The source object/text to search for numbers.

    Returns:
        A list of all integers found.

    """
    return [int(num) for num in re.findall(r"\d+", str(text))]


def get_browser(name: str = "gc", *, headless: bool = False, show_images: bool = False) -> Browser:  # noqa: ARG001
    """Create and return an easelenium Browser instance with a clean session profile.

    Args:
        name: The browser driver name (default is "gc" for Google Chrome).
        headless: Whether to run the browser in headless mode.
        show_images: Whether to allow loading images.

    Returns:
        An initialized Browser instance.

    """
    browser_name = name

    profile_path = Path(gettempdir()) / f"{name}_session"
    webdriver_kwargs = {
        "uc": True,
        "uc_subprocess": True,
        "do_not_track": True,
        "user_data_dir": str(profile_path),
    }

    return Browser(browser_name, headless=headless, webdriver_kwargs=webdriver_kwargs)


def browser_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorate a function to automatically manage browser lifecycle.

    Injects a Browser instance into the kwargs if one is not provided,
    and ensures it is correctly cleaned up (quit) at the end. Takes a
    screenshot on failure.

    Args:
        func: The function to decorate.

    Returns:
        The wrapped function.

    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        """Wrap the decorated function and manage its browser instance."""
        browser = None
        return_value = None
        browser_was_created = False
        try:
            # NOTE: default kwargs are lost!!!
            browser = kwargs.get("browser")
            is_debug = os.environ.get("DEBUG", "").lower() in ("true", "1")
            if browser is None:
                browser = get_browser(
                    headless=not is_debug,
                    show_images=kwargs.get("show_images", not is_debug),
                )
                browser_was_created = True

            kwargs["browser"] = browser
            return_value = func(*args, **kwargs)
        except Exception:
            try:
                if browser:
                    browser.save_screenshot()
            except Exception:  # noqa: BLE001, S110
                pass
            raise
        finally:
            if browser and browser_was_created:
                browser.quit()

        return return_value

    return wrapper

