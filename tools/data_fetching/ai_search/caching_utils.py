"""Utilities for caching computed values to disk using pickle serialization."""

import hashlib
import os
import pickle
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

ENV_VAR_DISABLE_CACHED = "DISABLE_CACHED_VALUE"
_TMP_CACHE_FOLDER = "locpycache"


def get_hashsum(*args: Any) -> str:  # noqa: ANN401
    """Compute a SHA-256 hex digest from the string representations of the given arguments.

    Args:
        *args: Any number of values to hash together.

    Returns:
        A hex string of the SHA-256 digest.

    """
    m = hashlib.sha256()
    m.update(",".join([str(a) for a in args]).encode("utf-8"))
    return m.hexdigest()


def get_cached_value(
    hashsum: str,
    func_get_value: Callable[[], Any],
    folder: Path | None = None,
    *,
    extra_folders: list[Path | str] | None = None,
) -> Any:  # noqa: ANN401
    """Return a cached value from disk, computing and storing it if not yet cached.

    If the environment variable ``DISABLE_CACHED_VALUE`` is set to a truthy value,
    the cache is bypassed entirely and ``func_get_value`` is called directly.

    Args:
        hashsum: A unique identifier (e.g. from :func:`get_hashsum`) for the cached entry.
        func_get_value: A zero-argument callable that produces the value to cache.
        folder: Directory in which cache files are stored.
                Defaults to a ``locpycache`` subdirectory inside the system temp dir.
        extra_folders: Subfolders to append to the cache directory path.

    Returns:
        The cached or freshly computed value.

    """
    if bool(os.environ.get(ENV_VAR_DISABLE_CACHED)):
        return func_get_value()

    cache_folder = Path(tempfile.gettempdir()) / _TMP_CACHE_FOLDER if folder is None else folder

    if extra_folders:
        cache_folder = cache_folder.joinpath(*extra_folders)

    cache_folder.mkdir(parents=True, exist_ok=True)

    path = cache_folder / hashsum

    if not path.exists():
        data = func_get_value()
        path.write_bytes(pickle.dumps(data))

    data = pickle.loads(path.read_bytes())  # noqa: S301

    if data is None:
        data = func_get_value()
        path.write_bytes(pickle.dumps(data))

    return data


def has_cached_value(hashsum: str, folder: Path | None = None) -> bool:
    """Check whether a cache entry identified by ``hashsum`` exists on disk.

    Args:
        hashsum: The cache key to look up, typically produced by :func:`get_hashsum`.
        folder: Directory in which cache files are stored.
                Defaults to the system temp dir.

    Returns:
        ``True`` if the cache file exists, ``False`` otherwise.

    """
    cache_folder = Path(tempfile.gettempdir()) if folder is None else folder
    return (cache_folder / hashsum).exists()


def tmp_cached() -> Callable[..., Any]:
    """Temporary placeholder for a cache decorator.

    Raises:
        NotImplementedError: This function is not yet implemented.

    """
    raise NotImplementedError

