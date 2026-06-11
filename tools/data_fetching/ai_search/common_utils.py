import os
import re
from functools import wraps
from pathlib import Path
from tempfile import gettempdir

from easelenium.browser import Browser


def get_number(text):
    return get_numbers(text)[0]


def get_numbers(text):
    return [int(num) for num in re.findall(r"\d+", str(text))]


def get_browser(name: str = "gc", *, headless: bool = False, show_images: bool = False):
    browser_name = name

    profile_path = Path(gettempdir()) / f"{name}_session"
    webdriver_kwargs = {
        "uc": True,
        "uc_subprocess": True,
        "do_not_track": True,
        "user_data_dir": str(profile_path),
    }

    return Browser(browser_name, headless=headless, webdriver_kwargs=webdriver_kwargs)


def browser_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        browser = None
        return_value = None
        browser_was_created = False
        try:
            # NOTE: default kwargs are lost!!!
            browser = kwargs.get("browser")
            is_debug = bool(os.environ.get("DEBUG", False))
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
            except:
                pass
            raise
        finally:
            if browser and browser_was_created:
                browser.quit()

        return return_value

    return wrapper
