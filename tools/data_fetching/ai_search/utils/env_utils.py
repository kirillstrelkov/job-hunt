"""Utility functions for retrieving environment variables and credentials."""

import os
from dataclasses import dataclass


@dataclass
class Credentials:
    """Credentials data structure holding username and password."""

    username: str
    password: str


def get_credentials(prefix: str) -> Credentials:
    """Retrieve username and password from environment variables using the prefix.

    Args:
        prefix: Prefix for the password environment variable (e.g. 'INDEED').

    Returns:
        Credentials containing the username and password.

    """
    username_key = "EMAIL"
    password_key = f"{prefix}_PASSWORD".upper()
    for key in [username_key, password_key]:
        if key not in os.environ:
            msg = f"{key} not found in environment variables"
            raise ValueError(msg)

    return Credentials(
        username=os.environ[username_key],
        password=os.environ[password_key],
    )
