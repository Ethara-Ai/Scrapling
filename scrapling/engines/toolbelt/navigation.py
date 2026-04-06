"""
Functions related to files and URLs
"""

from urllib.parse import urlparse

from playwright.async_api import Route as async_Route
from msgspec import Struct, structs, convert, ValidationError
from playwright.sync_api import Route

from scrapling.core.utils import log
from scrapling.core._types import Dict, Set, Tuple, Optional, Callable
from scrapling.engines.constants import EXTRA_RESOURCES


class ProxyDict(Struct):
    server: str
    username: str = ""
    password: str = ""


def create_intercept_handler(disable_resources: bool, blocked_domains: Optional[Set[str]] = None) -> Callable:
    """Create a route handler that blocks both resource types and specific domains.

    :param disable_resources: Whether to block default resource types.
    :param blocked_domains: Set of domain names to block requests to.
    :return: A sync route handler function.
    """
    pass


def create_async_intercept_handler(disable_resources: bool, blocked_domains: Optional[Set[str]] = None) -> Callable:
    """Create an async route handler that blocks both resource types and specific domains.

    :param disable_resources: Whether to block default resource types.
    :param blocked_domains: Set of domain names to block requests to.
    :return: An async route handler function.
    """
    pass


def construct_proxy_dict(proxy_string: str | Dict[str, str] | Tuple) -> Dict:
    """Validate a proxy and return it in the acceptable format for Playwright
    Reference: https://playwright.dev/python/docs/network#http-proxy

    :param proxy_string: A string or a dictionary representation of the proxy.
    :return:
    """
    pass
